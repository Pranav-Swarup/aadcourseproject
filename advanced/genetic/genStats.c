#include "bin-packing.h"
#include "population.h"
#include "chromosome.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>
#include<math.h>

#define POP_SZ 50

static const char *basename_of(const char *path) {
    const char *p = strrchr(path, '/');
    return p ? p + 1 : path;
}

static int bin_cmp(const void *a, const void *b) {
    const bin_t *av = *(bin_t **)a;
    const bin_t *bv = *(bin_t **)b;
    if (av->fill < bv->fill) return -1;
    if (av->fill > bv->fill) return 1;
    return 0;
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <input-file>\n", argv[0]);
        return 2;
    }
    const char *inpath = argv[1];
    FILE *in = fopen(inpath, "r");
    if (!in) {
        perror("fopen input");
        return 3;
    }

    size_t num_problems = 0;
    if (fscanf(in, " %zu", &num_problems) != 1) {
        fprintf(stderr, "Failed to read number of problems\n");
        fclose(in);
        return 4;
    }

    srand((unsigned)time(NULL));

    for (size_t p = 0; p < num_problems; p++) {
        char prob_id[256];
        if (fscanf(in, " %255s", prob_id) != 1) {
            fprintf(stderr, "Failed to read problem id for problem %zu\n", p);
            break;
        }
        long double bin_capacity;
        size_t num_items, optimal_num_bins;
        if (fscanf(in, " %Lf %zu %zu", &bin_capacity, &num_items, &optimal_num_bins) != 3) {
            fprintf(stderr, "Failed to read header for problem %s\n", prob_id);
            break;
        }
        long double *item_sizes = malloc(num_items * sizeof(*item_sizes));
        if (!item_sizes) { perror("malloc"); fclose(in); return 5; }
        for (size_t i = 0; i < num_items; i++) {
            if (fscanf(in, " %Lf", &item_sizes[i]) != 1) {
                fprintf(stderr, "Failed to read item %zu for problem %s\n", i, prob_id);
                free(item_sizes); fclose(in); return 6;
            }
        }

        /* build output filename: <inputbasename>_<problemId>.csv */
        const char *inbase = basename_of(inpath);
        size_t outlen = strlen(inbase) + 1 + strlen(prob_id) + 5 + 1; /* '_' + ".csv" + NUL */
        char *outname = malloc(outlen);
        if (!outname) { perror("malloc"); free(item_sizes); fclose(in); return 7; }
        snprintf(outname, outlen, "%s_%s.csv", inbase, prob_id);

        FILE *out = fopen(outname, "w");
        if (!out) { perror("fopen out"); free(outname); free(item_sizes); fclose(in); return 8; }

        fprintf(out, "gen,avg_fitness,best_num_bins,best_fitness,cum_secs\n");

        /* GA parameters (match main.c defaults) */
        size_t max_generations = 1000000;
        size_t population_size = POP_SZ;
        size_t mating_pool_size = POP_SZ;
        double max_mutation_rate = 0.1;
        double tournament_p = 1.0;
        unsigned tournament_size = 2;
        bool use_inversion = true;
        double max_secs = 1.0;

        clock_t start = clock();

        /* initialize population */
        pop_t *pop = pop_rand_init(bin_capacity, population_size, item_sizes, num_items);

        const chrom_t *best = pop->chroms[0];
        for (size_t i = 1; i < pop->num_chroms; i++) {
            if (pop->chroms[i]->fitness > best->fitness) best = pop->chroms[i];
        }

        /* write generation 1 stats */
        double endsec = ((double)clock() - start) * (1.0 / CLOCKS_PER_SEC);
        double avg = 0.0;
        for (size_t i = 0; i < pop->num_chroms; i++) avg += pop->chroms[i]->fitness;
        avg /= (double)pop->num_chroms;
        fprintf(out, "%zu,%lf,%zu,%lf,%lf\n", 1, avg, best->num_bins, best->fitness, endsec);

        for (size_t gen = 1; gen < max_generations; gen++) {
            /* termination checks */
            endsec = ((double)clock() - start) * (1.0 / CLOCKS_PER_SEC);
            if ((best->fitness >= nextafter(1.0, 0.0)) || (best->num_bins <= optimal_num_bins) || (endsec >= max_secs)) {
                break;
            }

            /* tournament selection */
            pop_t *mp = pop_alloc(mating_pool_size);
            for (size_t i = 0; i < mating_pool_size; i++) {
                mp->chroms[i] = pop->chroms[rand() % pop->num_chroms];
                for (unsigned j = 1; j < tournament_size; j++) {
                    size_t k = rand() % pop->num_chroms;
                    if (mp->chroms[i]->fitness < pop->chroms[k]->fitness) mp->chroms[i] = pop->chroms[k];
                }
            }

            /* child population */
            pop_t *child = pop_alloc(population_size);
            child->chroms[0] = chrom_copy(best);
            for (size_t i = 1; i < child->num_chroms; i++) {
                size_t i1 = rand() % mp->num_chroms;
                size_t i2 = rand() % mp->num_chroms;
                child->chroms[i] = chrom_cx(mp->chroms[i1], mp->chroms[i2], item_sizes, num_items);
            }
            free(mp);

            if (use_inversion) {
                for (size_t i = 1; i < child->num_chroms; i++) {
                    qsort(child->chroms[i]->bins, child->chroms[i]->num_bins, sizeof(*child->chroms[i]->bins), bin_cmp);
                }
            }

            for (size_t i = 1; i < child->num_chroms; i++) {
                chrom_mutate(child->chroms[i], max_mutation_rate, item_sizes, num_items);
            }

            /* find new best */
            const chrom_t *new_best = child->chroms[0];
            for (size_t i = 1; i < child->num_chroms; i++) {
                if (child->chroms[i]->fitness > new_best->fitness) new_best = child->chroms[i];
            }

            /* advance time and print stats for this generation */
            endsec = ((double)clock() - start) * (1.0 / CLOCKS_PER_SEC);
            avg = 0.0;
            for (size_t i = 0; i < child->num_chroms; i++) avg += child->chroms[i]->fitness;
            avg /= (double)child->num_chroms;
            fprintf(out, "%zu,%lf,%zu,%lf,%lf\n", gen + 1, avg, new_best->num_bins, new_best->fitness, endsec);

            pop_free(pop);
            pop = child;
            best = new_best;
        }

        pop_free(pop);
        fclose(out);
        free(outname);
        free(item_sizes);
    }

    fclose(in);
    return 0;
}
