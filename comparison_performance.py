import os
import glob
import random
import numpy as np
import tenseal as ts

# --- CKKS context and helper function ---
def create_ckks_context():
    context = ts.context(
        scheme=ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60]  # CKKS modulus sizes
    )
    context.global_scale = 2**40  # Large scaling factor for precision
    context.generate_galois_keys()
    return context

context = create_ckks_context()

def split_into_shares(secret_vector):
    """Splits a fingerprint template into two secret shares."""
    s2 = np.random.rand(*secret_vector.shape)
    s1 = secret_vector - s2
    return s1, s2

def compare_samples(probe, subject_id, template_filename):
    """Compares a probe against a template using CKKS encryption."""

    # 1) Split & scale the probe
    p1, p2 = split_into_shares(probe)

    # Encrypt the shares using CKKS
    #Enc_p1 = ts.ckks_vector(context, p1.tolist())
    #Enc_p2 = ts.ckks_vector(context, p2.tolist())
    Enc_p1 = p1
    Enc_p2 = p2

    # 2) Load & encrypt template shares
    s1_path = f"server1_iris_database/{subject_id}/{template_filename}"
    s2_path = f"server2_iris_database/{subject_id}/{template_filename}"
    t1 = np.load(s1_path)
    t2 = np.load(s2_path)

    #Enc_s1 = ts.ckks_vector(context, t1.tolist())
    #Enc_s2 = ts.ckks_vector(context, t2.tolist())
    Enc_s1 = t1
    Enc_s2 = t2

    # 3) Compute encrypted difference
    Enc_diff1 = Enc_s1 - Enc_p1
    Enc_diff2 = Enc_s2 - Enc_p2
    Enc_total_diff = Enc_diff1 + Enc_diff2

    # 4) Compute Euclidean distance
    Enc_sq_diff = Enc_total_diff * Enc_total_diff
    Enc_sq_sum = Enc_sq_diff.sum()

    # Decrypt and compute the final result
    #decrypted_sq_sum = Enc_sq_sum.decrypt()
    #distance = float(np.sqrt(decrypted_sq_sum[0]))  # Approximate due to CKKS
    distance = float(np.sqrt(Enc_sq_sum))
    return distance

def main():
    system_name = "iris_non-encrypted"

    db_root = "IrisFingerprintDatabases/IrisDatabase"
    subject_ids = sorted(os.listdir(db_root))

    mated_scores = []
    nonmated_scores = []

    all_files_dict = {}
    for subj in subject_ids:
        subj_path = os.path.join(db_root, subj)
        if os.path.isdir(subj_path):
            npy_files = sorted(glob.glob(os.path.join(subj_path, "*.npy")))
            all_files_dict[subj] = npy_files

    # Create a global pool for non-mated comparisons
    global_pool = [(sid, f) for sid, files in all_files_dict.items() for f in files]

    for subj in subject_ids:
        files_in_subj = all_files_dict.get(subj, [])
        if len(files_in_subj) < 5:
            continue  # Skip if fewer than 4 files

        chosen_files = files_in_subj[:5]

        # ========== Mated: Compare all pairwise combos within the first 4 ==========
        local_mated_scores = []
        for i in range(5):
            for j in range(i + 1, 5):
                template_path = chosen_files[i]
                probe_path = chosen_files[j]

                template_filename = os.path.basename(template_path)
                probe_array = np.load(probe_path)

                dist = compare_samples(probe_array, subj, template_filename)
                local_mated_scores.append(dist)

        K = len(local_mated_scores)  # typically 6
        if K == 0:
            continue

        # ========== Non-Mated: Pick exactly K random files from other subjects ==========
        other_files = [(sid, f) for sid, f in global_pool if sid != subj]
        random.shuffle(other_files)
        chosen_nonmated = other_files[:K]

        local_nonmated_scores = []
        for (other_sid, nfpath) in chosen_nonmated:
            template_filename = os.path.basename(chosen_files[0])  # Use first as template
            probe_array = np.load(nfpath)

            dist = compare_samples(probe_array, subj, template_filename)
            local_nonmated_scores.append(dist)

        # Store results
        mated_scores.extend(local_mated_scores)
        nonmated_scores.extend(local_nonmated_scores)

        print(f"Subject {subj}: +{K} mated, +{K} non-mated.")

    # Convert final results to arrays
    mated_scores = np.array(mated_scores)
    nonmated_scores = np.array(nonmated_scores)

    print(f"TOTAL Mated: {len(mated_scores)}")
    print(f"TOTAL Non-Mated: {len(nonmated_scores)}")

    # Save results
    mated_txt_file = f"{system_name}_mated.txt.gz"
    nonmated_txt_file = f"{system_name}_nonmated.txt.gz"

    np.savetxt(mated_txt_file, mated_scores, fmt="%.8f")
    np.savetxt(nonmated_txt_file, nonmated_scores, fmt="%.8f")

    print(f"Saved {len(mated_scores)} mated scores to {mated_txt_file}")
    print(f"Saved {len(nonmated_scores)} nonmated scores to {nonmated_txt_file}")

if __name__ == "__main__":
    main()