#include <algorithm>
#include <chrono>
#include <cmath>
#include <glpk.h>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <string>
#include <vector>

using namespace std;

struct Container {
  map<int, int> items;
  double size;
  int size_class; // 1=large, 2=medium, 3=small
};

struct Pattern {
  map<int, int> items; // Direct item packing (simplified from containers)
  double value;
};

struct Instance {
  int n;
  vector<double> sizes;
  vector<int> demands;
  double bin_capacity;
};

class HobergRothvossAlgorithm {
private:
  Instance instance;
  vector<Pattern> patterns;
  vector<double> x;
  double w;
  mt19937 rng;

  int get_size_class(double size) {
    if (size > w / 2.0)
      return 1;
    if (size > w / 6.0)
      return 2;
    return 3;
  }

  Pattern solve_knapsack(const vector<double> &values) {
    int n = instance.n;
    vector<vector<double>> dp(n + 1, vector<double>(int(w) + 1, 0.0));
    vector<vector<int>> choice(n + 1, vector<int>(int(w) + 1, 0));

    for (int i = 1; i <= n; i++) {
      for (int cap = 0; cap <= int(w); cap++) {
        dp[i][cap] = dp[i - 1][cap];
        choice[i][cap] = 0;

        int max_copies =
            min((int)(cap / instance.sizes[i - 1]), instance.demands[i - 1]);
        for (int k = 1; k <= max_copies; k++) {
          int remaining = cap - k * int(instance.sizes[i - 1]);
          double value = dp[i - 1][remaining] + k * values[i - 1];
          if (value > dp[i][cap]) {
            dp[i][cap] = value;
            choice[i][cap] = k;
          }
        }
      }
    }

    Pattern patt;
    int cap = int(w);
    for (int i = n; i >= 1; i--) {
      if (choice[i][cap] > 0) {
        patt.items[i - 1] = choice[i][cap];
        cap -= choice[i][cap] * int(instance.sizes[i - 1]);
      }
    }
    patt.value = dp[n][int(w)];

    return patt;
  }

  void solve_gilmore_gomory_lp() {
    patterns.clear();
    x.clear();

    // Initial patterns
    for (int i = 0; i < instance.n; i++) {
      Pattern p;
      p.items[i] = 1;
      p.value = 0.0;
      patterns.push_back(p);
      x.push_back(0.0);
    }

    int iteration = 0;
    const int MAX_ITER = 100;

    while (iteration < MAX_ITER) {
      iteration++;

      glp_prob *lp = glp_create_prob();
      glp_set_obj_dir(lp, GLP_MIN);

      int num_patterns = patterns.size();

      glp_add_rows(lp, instance.n);
      for (int i = 0; i < instance.n; i++) {
        glp_set_row_bnds(lp, i + 1, GLP_LO, instance.demands[i], 0.0);
      }

      glp_add_cols(lp, num_patterns);
      for (int j = 0; j < num_patterns; j++) {
        glp_set_col_bnds(lp, j + 1, GLP_LO, 0.0, 0.0);
        glp_set_obj_coef(lp, j + 1, 1.0);
      }

      vector<int> ia, ja;
      vector<double> ar;
      ia.push_back(0);
      ja.push_back(0);
      ar.push_back(0.0);

      for (int i = 0; i < instance.n; i++) {
        for (int j = 0; j < num_patterns; j++) {
          if (patterns[j].items.count(i) > 0) {
            ia.push_back(i + 1);
            ja.push_back(j + 1);
            ar.push_back(patterns[j].items[i]);
          }
        }
      }

      glp_load_matrix(lp, ar.size() - 1, ia.data(), ja.data(), ar.data());

      glp_smcp parm;
      glp_init_smcp(&parm);
      parm.msg_lev = GLP_MSG_OFF;
      glp_simplex(lp, &parm);

      vector<double> duals(instance.n);
      for (int i = 0; i < instance.n; i++) {
        duals[i] = glp_get_row_dual(lp, i + 1);
      }

      x.clear();
      x.resize(num_patterns, 0.0);
      for (int j = 0; j < num_patterns; j++) {
        x[j] = glp_get_col_prim(lp, j + 1);
        patterns[j].value = x[j];
      }

      glp_delete_prob(lp);

      Pattern new_patt = solve_knapsack(duals);
      double reduced_cost = 1.0 - new_patt.value;

      if (reduced_cost >= -1e-6 || new_patt.items.empty()) {
        break;
      }

      new_patt.value = 0.0;
      patterns.push_back(new_patt);
      x.push_back(0.0);
    }

    cout << "Column generation: " << iteration << " iterations, "
         << patterns.size() << " patterns" << endl;
  }

  // 2015 STEP 1: Rebuild containers for smoothness
  void rebuild_containers() {
    cout << "Rebuilding containers (2015 improvement)..." << endl;

    int rebuilt = 0;

    for (int p = 0; p < patterns.size(); p++) {
      if (x[p] < 1e-9)
        continue;

      // Check item multiplicity by size class
      map<int, map<int, int>>
          size_class_items; // size_class -> item_id -> count

      for (auto &item_pair : patterns[p].items) {
        int item_id = item_pair.first;
        int count = item_pair.second;
        int sc = get_size_class(instance.sizes[item_id]);
        size_class_items[sc][item_id] = count;
      }

      // For each size class, check if any item appears too often
      for (auto &sc_pair : size_class_items) {
        int sigma = sc_pair.first;
        double threshold = pow(1.0 / sigma, 0.25) * 10; // Practical threshold

        for (auto &item_pair : sc_pair.second) {
          int item_id = item_pair.first;
          int count = item_pair.second;

          if (count > threshold) {
            // Reduce multiplicity
            patterns[p].items[item_id] = (int)threshold;
            rebuilt++;
          }
        }
      }
    }

    if (rebuilt > 0) {
      cout << "Rebuilt " << rebuilt << " item assignments for smoothness."
           << endl;
    }
  }

  // 2015 STEP 2: Full spectrum Lovett-Meka
  void lovett_meka_full_spectrum() {
    cout << "Lovett-Meka with full spectrum (2015 improvement)..." << endl;

    int n = patterns.size();
    vector<double> lambdas(n);

    // Full spectrum: lambda_i = 1/sqrt(log(n))
    double base_lambda = 1.0 / sqrt(log(max(2, n)));
    for (int i = 0; i < n; i++) {
      lambdas[i] = base_lambda;
    }

    uniform_real_distribution<double> dist(0.0, 1.0);
    int rounded = 0;

    for (int i = 0; i < x.size(); i++) {
      if (x[i] > 1e-9 && x[i] < 1.0 - 1e-9) {
        double lambda = lambdas[min(i, (int)lambdas.size() - 1)];
        double prob = x[i] + lambda * (dist(rng) - 0.5);
        prob = max(0.0, min(1.0, prob));

        x[i] = (dist(rng) < prob) ? 1.0 : 0.0;
        patterns[i].value = x[i];
        rounded++;
      } else if (x[i] >= 1.0 - 1e-9) {
        x[i] = ceil(x[i]);
        patterns[i].value = x[i];
      } else {
        x[i] = 0.0;
        patterns[i].value = 0.0;
      }
    }

    cout << "Rounded " << rounded << " fractional variables." << endl;
  }

public:
  HobergRothvossAlgorithm(const Instance &inst) : instance(inst), rng(42) {
    w = inst.bin_capacity;
  }

  vector<double> run() {
    cout << "\n=== STEP 0: 2-STAGE LP (simplified as Gilmore-Gomory) ==="
         << endl;
    solve_gilmore_gomory_lp();

    cout << "\n=== STEP 1: REBUILD CONTAINERS (2015) ===" << endl;
    rebuild_containers();

    cout << "\n=== STEP 2: LOVETT-MEKA FULL SPECTRUM (2015) ===" << endl;
    lovett_meka_full_spectrum();

    return x;
  }

  void print_solution() {
    cout << "\n=== SOLUTION ===" << endl;
    double total = 0.0;
    int used = 0;

    for (int i = 0; i < x.size(); i++) {
      if (x[i] > 1e-9) {
        used++;
        total += x[i];
      }
    }

    cout << "Patterns used: " << used << endl;
    cout << "Total bins: " << total << endl;

    int shown = 0;
    cout << "\nFirst 20 patterns:" << endl;
    for (int i = 0; i < x.size() && shown < 20; i++) {
      if (x[i] > 1e-9) {
        cout << "  Pattern " << i << ": " << x[i] << " bins - Items: ";
        for (auto &p : patterns[i].items) {
          cout << "(item_" << p.first << " x" << p.second << ") ";
        }
        cout << endl;
        shown++;
      }
    }

    if (used > 20) {
      cout << "  ... and " << (used - 20) << " more" << endl;
    }
  }
};

Instance generate_benchmark(int n, double cap) {
  Instance inst;
  inst.n = n;
  inst.bin_capacity = cap;

  for (int i = 0; i < n / 3; i++) {
    inst.sizes.push_back(cap * (0.4 + 0.1 * (i % 10) / 10.0));
    inst.demands.push_back(100 + (i * 13) % 200);
  }
  for (int i = 0; i < n / 3; i++) {
    inst.sizes.push_back(cap * (0.2 + 0.15 * (i % 10) / 10.0));
    inst.demands.push_back(200 + (i * 17) % 300);
  }
  for (int i = 0; i < n - 2 * (n / 3); i++) {
    inst.sizes.push_back(cap * (0.05 + 0.1 * (i % 10) / 10.0));
    inst.demands.push_back(300 + (i * 19) % 400);
  }

  return inst;
}

void run_test(const string &name, const Instance &inst) {
  cout << "\n" << string(70, '=') << endl;
  cout << "=== " << name << " ===" << endl;
  cout << string(70, '=') << endl;

  double total_vol = 0.0;
  int total_items = 0;
  for (int i = 0; i < inst.n; i++) {
    total_vol += inst.sizes[i] * inst.demands[i];
    total_items += inst.demands[i];
  }

  cout << "Items: " << inst.n << " types, " << total_items << " total" << endl;
  cout << "Bin capacity: " << inst.bin_capacity << endl;
  cout << "Total volume: " << total_vol << endl;
  cout << "Lower bound: " << ceil(total_vol / inst.bin_capacity) << " bins"
       << endl;

  auto start = chrono::high_resolution_clock::now();

  HobergRothvossAlgorithm algo(inst);
  algo.run();

  auto end = chrono::high_resolution_clock::now();
  auto dur = chrono::duration_cast<chrono::milliseconds>(end - start);

  algo.print_solution();
  cout << "\nTime: " << dur.count() << " ms" << endl;
  cout << string(70, '=') << endl;
}

int main() {
  cout << "=============================================" << endl;
  cout << "  HOBERG-ROTHVOSS 2015 ALGORITHM" << endl;
  cout << "  (Simplified with 2015 improvements)" << endl;
  cout << "=============================================" << endl;

  //    run_test("BENCHMARK 40", generate_benchmark(40, 100.0));
  run_test("BENCHMARK 60", generate_benchmark(60, 100.0));

  return 0;
}

// Compile: g++ -o hr2015 rothvoss2015.cpp -lglpk -std=c++11
