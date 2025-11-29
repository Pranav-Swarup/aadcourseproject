#include <algorithm>
#include <chrono>
#include <cmath>
#include <glpk.h>
#include <iostream>
#include <map>
#include <random>
#include <string>
#include <vector>

using namespace std;

struct Pattern {
  map<int, int> items; // item_id -> count
  double value;
};

struct Instance {
  int n;                // number of item types
  vector<double> sizes; // size of each item type
  vector<int> demands;  // demand for each item type
  double bin_capacity;
};

class RothvossAlgorithm {
private:
  Instance instance;
  vector<Pattern> patterns;
  vector<double> x; // solution values
  int q;            // discretization parameter
  double w;         // bin capacity
  mt19937 rng;

  // Calculate q = polylog(n) for discretization
  int calculate_q() {
    int n = instance.n;
    // q = O(log^3(n)) as suggested in typical bin packing literature
    return max(10, (int)(pow(log(n), 3)));
  }

  // Solve knapsack to find new pattern with negative reduced cost
  Pattern solve_pricing_problem(const vector<double> &dual_prices) {
    // Solve knapsack: maximize sum(dual_prices[i] * x[i])
    // subject to: sum(sizes[i] * x[i]) <= bin_capacity

    int n = instance.n;
    vector<vector<double>> dp(n + 1, vector<double>(int(w) + 1, 0.0));
    vector<vector<int>> choice(n + 1, vector<int>(int(w) + 1, 0));

    // Dynamic programming for knapsack
    for (int i = 1; i <= n; i++) {
      for (int cap = 0; cap <= int(w); cap++) {
        dp[i][cap] = dp[i - 1][cap]; // Don't take item i-1
        choice[i][cap] = 0;

        // Try taking multiple copies of item i-1
        int max_copies = cap / int(instance.sizes[i - 1]);
        for (int k = 1; k <= max_copies && k <= instance.demands[i - 1]; k++) {
          int remaining_cap = cap - k * int(instance.sizes[i - 1]);
          double value = dp[i - 1][remaining_cap] + k * dual_prices[i - 1];
          if (value > dp[i][cap]) {
            dp[i][cap] = value;
            choice[i][cap] = k;
          }
        }
      }
    }

    // Reconstruct pattern
    Pattern new_pattern;
    int cap = int(w);
    for (int i = n; i >= 1; i--) {
      if (choice[i][cap] > 0) {
        new_pattern.items[i - 1] = choice[i][cap];
        cap -= choice[i][cap] * int(instance.sizes[i - 1]);
      }
    }
    new_pattern.value = dp[n][int(w)];

    return new_pattern;
  }

  // Solve standard Gilmore-Gomory LP using column generation
  void solve_standard_lp() {
    patterns.clear();
    x.clear();

    // Start with simple patterns (one item per bin)
    for (int i = 0; i < instance.n; i++) {
      Pattern p;
      p.items[i] = 1;
      p.value = 0.0;
      patterns.push_back(p);
      x.push_back(0.0);
    }

    // Column generation iterations
    int iteration = 0;
    const int MAX_ITERATIONS = 100;

    while (iteration < MAX_ITERATIONS) {
      iteration++;

      // Create and solve current LP
      glp_prob *lp = glp_create_prob();
      glp_set_prob_name(lp, "BinPacking");
      glp_set_obj_dir(lp, GLP_MIN);

      int num_patterns = patterns.size();

      // Add rows (constraints): one per item type
      glp_add_rows(lp, instance.n);
      for (int i = 0; i < instance.n; i++) {
        glp_set_row_bnds(lp, i + 1, GLP_LO, instance.demands[i], 0.0);
      }

      // Add columns (variables): one per pattern
      glp_add_cols(lp, num_patterns);
      for (int j = 0; j < num_patterns; j++) {
        glp_set_col_bnds(lp, j + 1, GLP_LO, 0.0, 0.0);
        glp_set_obj_coef(lp, j + 1, 1.0);
      }

      // Set constraint matrix
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

      // Solve LP
      glp_smcp parm;
      glp_init_smcp(&parm);
      parm.msg_lev = GLP_MSG_OFF;
      glp_simplex(lp, &parm);

      // Get dual prices
      vector<double> dual_prices(instance.n);
      for (int i = 0; i < instance.n; i++) {
        dual_prices[i] = glp_get_row_dual(lp, i + 1);
      }

      // Extract primal solution - resize x to match patterns
      x.clear();
      x.resize(num_patterns, 0.0);
      for (int j = 0; j < num_patterns; j++) {
        double val = glp_get_col_prim(lp, j + 1);
        x[j] = val;
        patterns[j].value = val;
      }

      glp_delete_prob(lp);

      // Solve pricing problem
      Pattern new_pattern = solve_pricing_problem(dual_prices);

      // Check if new pattern improves objective (reduced cost < -epsilon)
      double reduced_cost = 1.0 - new_pattern.value;

      if (reduced_cost >= -1e-6 || new_pattern.items.empty()) {
        // No improving pattern found, stop
        break;
      }

      // Add new pattern and extend x vector
      new_pattern.value = 0.0;
      patterns.push_back(new_pattern);
      x.push_back(0.0);
    }

    // Final sync: ensure x matches patterns size
    if (x.size() != patterns.size()) {
      x.resize(patterns.size(), 0.0);
    }

    cout << "Column generation completed in " << iteration << " iterations."
         << endl;
    cout << "Generated " << patterns.size() << " patterns total." << endl;
  }

  // STEP 1: Discretize values to multiples of 1/q
  void discretize_values() {
    // Make sure x vector matches patterns size
    if (x.size() != patterns.size()) {
      cout << "Warning: Resizing x from " << x.size() << " to "
           << patterns.size() << endl;
      x.resize(patterns.size(), 0.0);
    }

    for (int i = 0; i < x.size(); i++) {
      // Round to nearest multiple of 1/q
      x[i] = round(x[i] * q) / (double)q;
      patterns[i].value = x[i];
    }
  }

  // STEP 2: Group & Glue - handle spiky patterns
  void group_and_glue() {
    int new_item_id = instance.n;      // IDs for glued items
    map<int, double> glued_item_sizes; // Track sizes of glued items

    for (int p = 0; p < patterns.size(); p++) {
      if (x[p] < 1e-9)
        continue; // Skip unused patterns

      vector<int> items_to_process;
      for (auto &item : patterns[p].items) {
        items_to_process.push_back(item.first);
      }

      for (int item_id : items_to_process) {
        // Only process original items (not already glued items)
        if (item_id >= instance.n)
          continue;

        // Get item size
        double item_size = instance.sizes[item_id];

        // Check if item is "small" (< bin_capacity / 2)
        if (item_size < w / 2.0) {

          int count = patterns[p].items[item_id];

          // Check for spiky pattern: many copies of small item
          // Using a more reasonable threshold
          int threshold = max(10, (int)(w * q / 100)); // Adjusted threshold

          if (count >= threshold) {
            // GLUE: Combine multiple copies into fewer copies of larger item
            int copies_to_glue = (count / threshold) * threshold;
            int num_new_items = copies_to_glue / threshold;

            // Create new glued item
            double new_size = item_size * threshold;

            // Only glue if the new item fits in the bin
            if (new_size <= w) {
              // Remove glued copies of original item
              patterns[p].items[item_id] -= copies_to_glue;
              if (patterns[p].items[item_id] <= 0) {
                patterns[p].items.erase(item_id);
              }

              // Add glued item
              patterns[p].items[new_item_id] = num_new_items;
              glued_item_sizes[new_item_id] = new_size;

              new_item_id++;
            }
          }
        }
      }
    }

    if (new_item_id > instance.n) {
      cout << "Created " << (new_item_id - instance.n) << " glued items."
           << endl;
    }
  }

  // STEP 3: Lovett-Meka rounding algorithm (simplified version)
  void lovett_meka_rounding() {
    // This is a simplified implementation of the LM12 algorithm
    // Full implementation requires careful attention to the partial coloring
    // method

    uniform_real_distribution<double> dist(0.0, 1.0);

    for (int i = 0; i < x.size(); i++) {
      if (x[i] > 0 && x[i] < 1) {
        // Fractional value - round probabilistically
        double threshold = 0.5; // Simplified threshold

        if (dist(rng) < x[i]) {
          x[i] = ceil(x[i]);
        } else {
          x[i] = floor(x[i]);
        }

        patterns[i].value = x[i];
      }
    }
  }

public:
  RothvossAlgorithm(const Instance &inst) : instance(inst), rng(42) {
    w = inst.bin_capacity;
    q = calculate_q();
    cout << "Discretization parameter q = " << q << endl;
  }

  vector<double> run() {
    cout << "\n=== STEP 0: INITIALIZATION ===" << endl;
    cout << "Solving Gilmore-Gomory LP with column generation..." << endl;
    solve_standard_lp();

    cout << "\n=== STEP 1: DISCRETIZATION ===" << endl;
    discretize_values();
    cout << "Values discretized to multiples of 1/" << q << endl;

    cout << "\n=== STEP 2: GROUP & GLUE ===" << endl;
    group_and_glue();

    cout << "\n=== STEP 3: LOVETT-MEKA ROUNDING ===" << endl;
    lovett_meka_rounding();
    cout << "Rounding completed." << endl;

    return x;
  }

  void print_solution() {
    cout << "\n=== SOLUTION ===" << endl;
    double total_bins = 0.0;
    int patterns_used = 0;

    for (int i = 0; i < x.size(); i++) {
      if (x[i] > 1e-9) {
        patterns_used++;
        total_bins += x[i];
      }
    }

    cout << "Number of patterns used: " << patterns_used << endl;
    cout << "Total bins used: " << total_bins << endl;

    // Show first 20 non-zero patterns
    int shown = 0;
    cout << "\nFirst 20 patterns with non-zero values:" << endl;
    for (int i = 0; i < x.size() && shown < 20; i++) {
      if (x[i] > 1e-9) {
        cout << "  Pattern " << i << ": " << x[i] << " bins - Items: ";
        for (auto &item : patterns[i].items) {
          cout << "(item_" << item.first << " x " << item.second << ") ";
        }
        cout << endl;
        shown++;
      }
    }

    if (patterns_used > 20) {
      cout << "  ... and " << (patterns_used - 20) << " more patterns" << endl;
    }
  }
};

// Generate random instance
Instance generate_random_instance(int n, double bin_capacity, int seed = 42) {
  mt19937 rng(seed);
  uniform_real_distribution<double> size_dist(5.0, bin_capacity * 0.4);
  uniform_int_distribution<int> demand_dist(50, 500);

  Instance inst;
  inst.n = n;
  inst.bin_capacity = bin_capacity;

  for (int i = 0; i < n; i++) {
    inst.sizes.push_back(size_dist(rng));
    inst.demands.push_back(demand_dist(rng));
  }

  return inst;
}

// Generate benchmark instance (harder cases)
Instance generate_benchmark_instance(int n, double bin_capacity) {
  Instance inst;
  inst.n = n;
  inst.bin_capacity = bin_capacity;

  // Mix of item sizes:
  // - Large items (0.4 - 0.5 of capacity)
  // - Medium items (0.2 - 0.35 of capacity)
  // - Small items (0.05 - 0.15 of capacity)

  for (int i = 0; i < n / 3; i++) {
    inst.sizes.push_back(bin_capacity * (0.4 + 0.1 * (i % 10) / 10.0));
    inst.demands.push_back(100 + (i * 13) % 200);
  }

  for (int i = 0; i < n / 3; i++) {
    inst.sizes.push_back(bin_capacity * (0.2 + 0.15 * (i % 10) / 10.0));
    inst.demands.push_back(200 + (i * 17) % 300);
  }

  for (int i = 0; i < n - 2 * (n / 3); i++) {
    inst.sizes.push_back(bin_capacity * (0.05 + 0.1 * (i % 10) / 10.0));
    inst.demands.push_back(300 + (i * 19) % 400);
  }

  return inst;
}

void run_test(const string &name, const Instance &inst) {
  cout << "\n" << string(70, '=') << endl;
  cout << "=== TEST: " << name << " ===" << endl;
  cout << string(70, '=') << endl;

  cout << "\n=== BIN PACKING INSTANCE ===" << endl;
  cout << "Number of item types: " << inst.n << endl;
  cout << "Bin capacity: " << inst.bin_capacity << endl;

  // Print statistics
  double total_volume = 0.0;
  int total_items = 0;
  for (int i = 0; i < inst.n; i++) {
    total_volume += inst.sizes[i] * inst.demands[i];
    total_items += inst.demands[i];
  }

  cout << "Total items to pack: " << total_items << endl;
  cout << "Total volume: " << total_volume << endl;
  cout << "Theoretical lower bound (bins): "
       << ceil(total_volume / inst.bin_capacity) << endl;

  cout << "\nFirst 10 item types:" << endl;
  for (int i = 0; i < min(10, inst.n); i++) {
    cout << "  Item " << i << ": size=" << inst.sizes[i]
         << ", demand=" << inst.demands[i] << endl;
  }

  auto start = chrono::high_resolution_clock::now();

  RothvossAlgorithm algo(inst);
  vector<double> solution = algo.run();

  auto end = chrono::high_resolution_clock::now();
  auto duration = chrono::duration_cast<chrono::milliseconds>(end - start);

  algo.print_solution();

  cout << "\nExecution time: " << duration.count() << " ms" << endl;
  cout << string(70, '=') << endl;
}

int main() {
  // Test 1: Small instance
  //    Instance small = generate_random_instance(10, 100.0, 42);
  //    run_test("SMALL RANDOM (10 items)", small);

  // Test 2: Medium instance
  //    Instance medium = generate_random_instance(30, 150.0, 123);
  //    run_test("MEDIUM RANDOM (30 items)", medium);

  // Test 3: Large instance
  //    Instance large = generate_random_instance(50, 200.0, 456);
  //    run_test("LARGE RANDOM (50 items)", large);

  // Test 4: Benchmark with mixed sizes
  Instance benchmark = generate_benchmark_instance(60, 100.0);
  run_test("BENCHMARK MIXED SIZES (60 items)", benchmark);

  // Test 5: Very large instance
  //    Instance xlarge = generate_random_instance(100, 250.0, 789);
  //    run_test("EXTRA LARGE RANDOM (100 items)", xlarge);

  // Test 6: High demand instance
  Instance high_demand;
  high_demand.n = 40;
  high_demand.bin_capacity = 100.0;
  mt19937 rng(999);
  uniform_real_distribution<double> size_dist(8.0, 35.0);
  uniform_int_distribution<int> demand_dist(500, 2000);
  for (int i = 0; i < 40; i++) {
    high_demand.sizes.push_back(size_dist(rng));
    high_demand.demands.push_back(demand_dist(rng));
  }
  run_test("HIGH DEMAND (40 items, 500-2000 each)", high_demand);

  return 0;
}

// Compilation: g++ -o rothvoss rothvoss.cpp -lglpk -std=c++11
// Note: Requires GLPK library installed
