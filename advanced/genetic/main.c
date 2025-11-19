#include "bin-packing.h"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#define NUM_PASSES      25
#define POP_SZ          50

static int results_only = 0;

static void falk_main(void);

int main(int argc, char **argv) {
        for (int i = 1; i < argc; i++) {
                if ((strcmp(argv[i], "-results") == 0)
                    || (strcmp(argv[i], "--results") == 0)) {
                        results_only = 1;
                }
        }

        srand(time(NULL));
        falk_main();
        return 0;
}

static void falk_main_solve(void) {
        /* skip problem identifier */
        scanf(" %*s");
        long double bin_capacity;
        size_t num_items, optimal_num_bins;
        scanf(" %Lf %zu %zu",
              &bin_capacity, &num_items, &optimal_num_bins);
        long double *item_sizes = malloc(num_items
                                       * sizeof(*item_sizes));
        for (size_t i=0; i<num_items; i++) {
                scanf(" %Lf", item_sizes+i);
        }
        prob_set_t ps = {.item_sizes = item_sizes,
                         .num_items = num_items,
                         .bin_capacity = bin_capacity,
                         .max_generations = 1000000,
                         .terminal_num_bins = optimal_num_bins,
                         .max_secs = 1,
                         .population_size = POP_SZ,
                         .mating_pool_size = POP_SZ,
                         .max_mutation_rate = 0.1,
                         .tournament_p = 1.0,
                         .tournament_size = 2,
                         .use_inversion_operator = true,
                         .results_only = results_only};
        printf("OPTIMAL NUMBER OF BINS: %zu\n", optimal_num_bins);
        for (size_t i=0; i<NUM_PASSES; i++) {
                printf("PASS #%zu:\n", i);
                fprintf(stderr, "PASS #%zu:\n", i);
                result_t *res = bin_packing(&ps);
                if (results_only) {
                        printf("FINAL: #bins: %zu\t fitness: %lf\n",
                               res->num_bins, res->fitness);
                }
                result_free(res);
        }
        free(item_sizes);
}
static void falk_main(void) {
        size_t num_problems;
        scanf(" %zu", &num_problems);
        for (size_t i=0; i<num_problems; i++) {
                printf("PROBLEM #%zu:\n", i);
                fprintf(stderr, "PROBLEM #%zu:\n", i);
                falk_main_solve();
        }
}
