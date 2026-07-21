import os
import re
import sys
import inspect
import pandas as pd
import traceback

# Add project root to sys.path to enable backend imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def normalize(name):
    name = name.lower()
    for ext in ['.jpg', '.jpeg', '.png', '.bmp']:
        if name.endswith(ext):
            name = name[:-len(ext)]
    if name.endswith('_jpg') or name.endswith('_png') or name.endswith('_jpeg'):
        name = name[:-4]
    if '_jpg.rf.' in name:
        name = name.split('_jpg.rf.')[0]
    elif '_png.rf.' in name:
        name = name.split('_png.rf.')[0]
    elif '.rf.' in name:
        name = name.split('.rf.')[0]
    return "".join(c for c in name if c.isalnum())

def clean_and_tokenize(name):
    name_no_ext = name.split('.')[0]
    s = re.sub(r'[^a-zA-Z0-9]', ' ', name_no_ext)
    tokens = [t.lower() for t in s.split() if t]
    nums = [int(n) for n in re.findall(r'\d+', name_no_ext)]
    return tokens, nums

def find_dataset_and_csv():
    workspace = r"c:\Users\AYAN\.gemini\antigravity-ide\scratch\tree-vision-ai"
    user_dir = r"c:\Users\AYAN"
    
    dataset_dir = None
    csv_candidates = []
    
    # 1. Search for 'testing strees' folder
    search_roots = [workspace, user_dir]
    for b_dir in search_roots:
        if not os.path.exists(b_dir):
            continue
        base_depth = b_dir.lower().count(os.sep)
        for root, dirs, files in os.walk(b_dir):
            current_depth = root.lower().count(os.sep)
            if b_dir == user_dir and (current_depth - base_depth) > 3:
                dirs[:] = []
                continue
            if any(ignored in root.lower() for ignored in [".git", ".venv", "node_modules", ".next"]):
                dirs[:] = []
                continue
            
            # Check if this folder or a child is 'testing strees'
            if root.replace(os.sep, "/").lower().endswith("data/testing strees") or root.lower().endswith("testing strees"):
                dataset_dir = root
                break
        if dataset_dir:
            break
            
    if not dataset_dir:
        # Fallback to known path if search fails
        dataset_dir = r"c:\Users\AYAN\Flocard Tree AI\data\testing strees"
        
    print(f"Resolved 'testing strees' folder path: {dataset_dir}")
    if not os.path.exists(dataset_dir):
        print(f"ERROR: Dataset directory {dataset_dir} does not exist!")
        sys.exit(1)
        
    # 2. Search for CSV files matching pattern
    parent_dir = os.path.dirname(dataset_dir)
    search_csv_dirs = [dataset_dir, parent_dir]
    
    print("\nSearching for CSV files matching 'external_test_set_ground_truth*' or 'truth*'...")
    found_paths = set()
    for s_dir in search_csv_dirs:
        if not os.path.exists(s_dir):
            continue
        for f in os.listdir(s_dir):
            if f.endswith('.csv'):
                f_lower = f.lower()
                if "external_test_set_ground_truth" in f_lower or "truth" in f_lower:
                    full_p = os.path.abspath(os.path.join(s_dir, f))
                    found_paths.add(full_p)
                    
    # Also scan recursively inside dataset_dir just in case
    for root, dirs, files in os.walk(dataset_dir):
        for f in files:
            if f.endswith('.csv'):
                f_lower = f.lower()
                if "external_test_set_ground_truth" in f_lower or "truth" in f_lower:
                    full_p = os.path.abspath(os.path.join(root, f))
                    found_paths.add(full_p)
                    
    for p in found_paths:
        try:
            df_temp = pd.read_csv(p)
            row_count = len(df_temp)
            print(f"Candidate CSV: {p}")
            print(f"  - Row count (data rows): {row_count}")
            csv_candidates.append((p, df_temp, row_count))
        except Exception as e:
            print(f"Candidate CSV: {p} (Error reading: {e})")
            
    # Filter candidates with 167 rows
    target_candidates = [c for c in csv_candidates if c[2] == 167]
    
    if len(target_candidates) == 0:
        print("ERROR: Found no CSV file with exactly 167 rows!")
        sys.exit(1)
    elif len(target_candidates) == 1:
        selected_path, selected_df, _ = target_candidates[0]
        print(f"\nSelected ground truth CSV: {selected_path}")
        return dataset_dir, selected_path, selected_df
    else:
        # Multiple candidates with 167 rows, let's compare their contents
        print(f"\nFound {len(target_candidates)} candidates with 167 rows. Diffing them...")
        first_path, first_df, _ = target_candidates[0]
        all_identical = True
        for path, df_curr, _ in target_candidates[1:]:
            if not first_df.equals(df_curr):
                all_identical = False
                print(f"DISCREPANCY: CSV contents differ between:")
                print(f"  1. {first_path}")
                print(f"  2. {path}")
                
        if not all_identical:
            print("ERROR: Multiple CSV files have 167 rows but their contents differ. Stopping.")
            sys.exit(1)
        else:
            print("All 167-row CSV candidates are identical in content. Proceeding with:")
            print(f"  - {first_path}")
            return dataset_dir, first_path, first_df

def verify_detector_and_signature(dataset_dir):
    print("\n--- Verifying Tree Detector Signature and Running Test Prediction ---")
    try:
        from backend.models.tree_detector import detect_target_tree
    except Exception as e:
        print(f"ERROR: Failed to import detect_target_tree: {e}")
        traceback.print_exc()
        sys.exit(1)
        
    # Inspect signature and docstring
    sig = inspect.signature(detect_target_tree)
    doc = inspect.getdoc(detect_target_tree)
    print(f"Function signature: detect_target_tree{sig}")
    print(f"Docstring snippet:\n{doc[:200]}...")
    
    # We need a single known-good image path from the dataset
    test_image_path = None
    for root, dirs, files in os.walk(dataset_dir):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                test_image_path = os.path.join(root, f)
                break
        if test_image_path:
            break
            
    print(f"Running single-image verification on: {test_image_path}")
    if not test_image_path or not os.path.exists(test_image_path):
        print("ERROR: Could not find any test image in the dataset to run verification.")
        sys.exit(1)
        
    try:
        res = detect_target_tree(test_image_path)
    except Exception as e:
        print(f"ERROR: Call to detect_target_tree() failed: {e}")
        traceback.print_exc()
        sys.exit(1)
        
    print(f"Test run output structure: {type(res)}")
    print(f"Returned dict keys: {list(res.keys())}")
    print(f"Returned values snippet: {str(res)[:300]}...")
    
    # Validate expected fields
    expected_keys = ["status", "crop_box", "image_context", "detected_tree_count", "all_boxes"]
    missing = [k for k in expected_keys if k not in res]
    if missing:
        print(f"ERROR: Returned dictionary is missing expected keys: {missing}")
        sys.exit(1)
        
    print("Verification SUCCESSFUL: Output structure matches assumptions!")
    return detect_target_tree

def main():
    # 1. Locate dataset and select CSV
    dataset_dir, csv_path, df = find_dataset_and_csv()
    
    # 2. Verify detector function signature and return values
    detect_func = verify_detector_and_signature(dataset_dir)
    
    # 3. Index all image files
    print("\nIndexing image files recursively in splits...")
    img_extensions = ('.jpg', '.jpeg', '.png', '.bmp')
    indexed_images = {} # normalized_key -> list of (full_path, split_folder)
    
    for split in ['test', 'train', 'valid']:
        split_path = os.path.join(dataset_dir, split)
        if not os.path.exists(split_path):
            print(f"WARNING: Split directory {split_path} does not exist!")
            continue
            
        for root, dirs, files in os.walk(split_path):
            for f in files:
                if f.lower().endswith(img_extensions):
                    full_p = os.path.join(root, f)
                    norm_k = normalize(f)
                    if norm_k not in indexed_images:
                        indexed_images[norm_k] = []
                    indexed_images[norm_k].append((full_p, split, f))
                    
    total_indexed = sum(len(v) for v in indexed_images.values())
    print(f"Indexed {total_indexed} files across {len(indexed_images)} distinct keys.")
    
    # 4. Perform fuzzy matching and record match statistics
    print("\nResolving mappings and checking matches...")
    match_audit = []
    unmatched_filenames = []
    ambiguous_matches = []
    
    resolved_mapping = {} # csv_idx -> (image_path, split, filename_in_dir)
    
    for idx, row in df.iterrows():
        csv_filename = row['filename']
        csv_toks, csv_nums = clean_and_tokenize(csv_filename)
        csv_norm_key = normalize(csv_filename)
        
        # Look for candidates
        candidates = []
        
        # Check direct normalized key match first
        if csv_norm_key in indexed_images:
            for full_p, split, f_in_dir in indexed_images[csv_norm_key]:
                candidates.append((full_p, split, f_in_dir, "exact_normalized_key", 1.0))
                
        # If no candidates, try fuzzy matching
        if not candidates:
            for norm_k, img_list in indexed_images.items():
                for full_p, split, f_in_dir in img_list:
                    # Clean Roboflow suffix from df_name
                    base_df_name = f_in_dir.split('_jpg.rf.')[0].split('_png.rf.')[0].split('.rf.')[0]
                    df_toks, df_nums = clean_and_tokenize(base_df_name)
                    
                    # Ignore '1' from 'tree_1'
                    df_nums_clean = [n for n in df_nums if n != 1]
                    if not df_nums_clean and 1 in df_nums:
                        df_nums_clean = [1]
                        
                    csv_nums_clean = [n for n in csv_nums if n != 1]
                    if not csv_nums_clean and 1 in csv_nums:
                        csv_nums_clean = [1]
                        
                    # Check numbers match
                    num_match = False
                    if csv_nums_clean and df_nums_clean:
                        if csv_nums_clean[-1] == df_nums_clean[-1]:
                            num_match = True
                    elif not csv_nums_clean and not df_nums_clean:
                        num_match = True
                        
                    if num_match:
                        # Check genus/species token overlap
                        if csv_toks and df_toks and csv_toks[0] == df_toks[0]:
                            overlap = len(set(csv_toks) & set(df_toks))
                            candidates.append((full_p, split, f_in_dir, "fuzzy_token_numeric", float(overlap)))
                            
            # Filter matches if multiple by token overlap
            if len(candidates) > 1:
                max_score = max(c[4] for c in candidates)
                candidates = [c for c in candidates if c[4] == max_score]
                
        # Classify the matches
        if len(candidates) == 0:
            unmatched_filenames.append({"csv_filename": csv_filename})
        elif len(candidates) > 1:
            # Ambiguous match
            ambiguous_matches.append({
                "csv_filename": csv_filename,
                "candidates": "; ".join([f"[{c[1]}] {c[2]}" for c in candidates])
            })
        else:
            full_p, split, f_in_dir = candidates[0][0], candidates[0][1], candidates[0][2]
            resolved_mapping[idx] = (full_p, split, f_in_dir)
            
            # If it's a fuzzy match, log to match_audit
            # Exact is defined as csv filename prefix matching the directory image prefix
            csv_prefix = csv_filename.split('.')[0].lower().replace('-', '_').replace(' ', '_')
            f_dir_prefix = f_in_dir.split('_jpg.rf.')[0].split('_png.rf.')[0].split('.rf.')[0].lower().replace('-', '_').replace(' ', '_')
            
            # Also clean double underscores
            csv_prefix = re.sub(r'_+', '_', csv_prefix)
            f_dir_prefix = re.sub(r'_+', '_', f_dir_prefix)
            
            is_exact = (csv_prefix == f_dir_prefix)
            if not is_exact:
                match_audit.append({
                    "csv_filename": csv_filename,
                    "matched_file_path": full_p,
                    "match_method": candidates[0][3],
                    "match_score_or_basis": f"score: {candidates[0][4]}, dir_prefix: {f_dir_prefix}, csv_prefix: {csv_prefix}"
                })
                
    # Save mapping audit tables
    os.makedirs("data", exist_ok=True)
    pd.DataFrame(match_audit).to_csv("data/match_audit.csv", index=False)
    pd.DataFrame(unmatched_filenames).to_csv("data/unmatched_filenames.csv", index=False)
    pd.DataFrame(ambiguous_matches).to_csv("data/ambiguous_matches.csv", index=False)
    
    print(f"Mapping complete:")
    print(f"  - Total CSV rows: {len(df)}")
    print(f"  - Successfully resolved matches: {len(resolved_mapping)}")
    print(f"  - Fuzzy matches audited to data/match_audit.csv: {len(match_audit)}")
    print(f"  - Unmatched filenames logged to data/unmatched_filenames.csv: {len(unmatched_filenames)}")
    print(f"  - Ambiguous matches logged to data/ambiguous_matches.csv: {len(ambiguous_matches)}")
    
    # 5. Run prediction over matched dataset
    print("\n--- Running detector predictions ---")
    
    prediction_cache = {} # resolved_file_path -> prediction_dict
    comparison_table = []
    
    unsure_count = 0
    skipped_count = 0
    
    for idx, row in df.iterrows():
        csv_filename = row['filename']
        category = row['category']
        confidence_easy_or_hard = row['confidence_easy_or_hard']
        gt_present = str(row['target_tree_present']).strip()
        
        # Normalize Ground Truth
        if gt_present.lower() == 'yes':
            gt_norm = 'Yes'
        elif gt_present.lower() == 'no':
            gt_norm = 'No'
        elif gt_present.lower() == 'unsure':
            gt_norm = 'Unsure'
            unsure_count += 1
        else:
            gt_norm = 'Unknown'
            
        if idx not in resolved_mapping:
            skipped_count += 1
            continue
            
        full_p, split, f_in_dir = resolved_mapping[idx]
        
        # Run prediction or fetch from cache
        if full_p not in prediction_cache:
            try:
                res = detect_func(full_p)
                prediction_cache[full_p] = res
            except Exception as e:
                print(f"BUG WARNING: Exception in detect_target_tree() on {full_p}: {e}")
                prediction_cache[full_p] = {
                    "status": "detector_bug_crash",
                    "crop_box": None,
                    "image_context": None,
                    "detected_tree_count": 0,
                    "all_boxes": [],
                    "error": str(e)
                }
                
        pred_res = prediction_cache[full_p]
        status = pred_res.get("status", "unknown")
        detected_count = pred_res.get("detected_tree_count", 0)
        
        # A tree is predicted as present if detected_tree_count > 0
        if status in ["detector_bug_crash", "detector_unavailable"]:
            pred_present = "No"
            print(f"BUG WARNING: Detector returned status '{status}' for {full_p}")
        else:
            pred_present = "Yes" if detected_count > 0 else "No"
            
        match_bool = (gt_norm == pred_present)
        
        comparison_table.append({
            "filename": csv_filename,
            "split_folder": split,
            "ground_truth": gt_norm,
            "prediction": pred_present,
            "match": match_bool,
            "category": category,
            "confidence_easy_or_hard": confidence_easy_or_hard,
            "status": status,
            "detected_tree_count": detected_count,
            "resolved_file_path": full_p
        })
        
    comp_df = pd.DataFrame(comparison_table)
    comp_df.to_csv("data/detector_evaluation_results.csv", index=False)
    print(f"Saved full comparison table to data/detector_evaluation_results.csv")
    
    # 6. Compute Accuracy and Breakdowns
    print("\n================ EVALUATION SUMMARY ================")
    
    valid_gt_mask = comp_df['ground_truth'].isin(['Yes', 'No'])
    valid_gt_df = comp_df[valid_gt_mask]
    
    is_test_mask = valid_gt_df['split_folder'] == 'test'
    is_leakage_mask = valid_gt_df['split_folder'].isin(['train', 'valid'])
    
    test_eval_df = valid_gt_df[is_test_mask]
    leakage_eval_df = valid_gt_df[is_leakage_mask]
    
    # Headline accuracy on test set only
    headline_total = len(test_eval_df)
    if headline_total > 0:
        headline_correct = test_eval_df['match'].sum()
        headline_acc = headline_correct / headline_total
        print(f"HEADLINE ACCURACY (test split only, excluding Unsure): {headline_acc:.2%} ({headline_correct}/{headline_total})")
    else:
        print("HEADLINE ACCURACY (test split only): N/A (0 images in test split)")
        
    # Leakage accuracy
    leakage_total = len(leakage_eval_df)
    if leakage_total > 0:
        leakage_correct = leakage_eval_df['match'].sum()
        leakage_acc = leakage_correct / leakage_total
        print(f"\n[LEAKAGE WARNING] Train/Valid Split Accuracy: {leakage_acc:.2%} ({leakage_correct}/{leakage_total})")
        print(f"  - Flagged: {leakage_total} images evaluated came from train/valid splits!")
        print("  - These splits might have been seen by the detector during training.")
    else:
        print("\nNo leakage: 0 images from train/valid splits in evaluation.")
        
    # Stats on Unsure ground truth
    unsure_eval_df = comp_df[comp_df['ground_truth'] == 'Unsure']
    print(f"\nUnsure Ground Truth rows (reported separately): {len(unsure_eval_df)}")
    if len(unsure_eval_df) > 0:
        pos_pred_unsure = (unsure_eval_df['prediction'] == 'Yes').sum()
        print(f"  - Detector predicted tree 'Yes' on {pos_pred_unsure} of {len(unsure_eval_df)} unsure images ({pos_pred_unsure / len(unsure_eval_df):.2%})")
        
    print("\n--- TEST SPLIT ONLY ACCURACY BREAKDOWNS ---")
    print_breakdowns(test_eval_df)
    
    print("\n--- OVERALL ACCURACY BREAKDOWNS (ALL SPLITS) ---")
    print_breakdowns(valid_gt_df)
    
    print("\n--- ERROR RATE ANALYSIS (OVERALL DATASET) ---")
    
    # Hard Negatives FPR
    hn_df = valid_gt_df[(valid_gt_df['category'] == 'hard_negatives')]
    hn_neg = hn_df[hn_df['ground_truth'] == 'No']
    if len(hn_neg) > 0:
        hn_fp = (hn_neg['prediction'] == 'Yes').sum()
        hn_fpr = hn_fp / len(hn_neg)
        print(f"False Positive Rate on 'hard_negatives' (GT=No): {hn_fpr:.2%} ({hn_fp}/{len(hn_neg)})")
    else:
        print("False Positive Rate on 'hard_negatives': N/A (0 negative images in category)")
        
    # Occluded Trees FNR
    occ_df = valid_gt_df[(valid_gt_df['category'] == 'occluded_trees')]
    occ_pos = occ_df[occ_df['ground_truth'] == 'Yes']
    if len(occ_pos) > 0:
        occ_fn = (occ_pos['prediction'] == 'No').sum()
        occ_fnr = occ_fn / len(occ_pos)
        print(f"False Negative Rate on 'occluded_trees' (GT=Yes): {occ_fnr:.2%} ({occ_fn}/{len(occ_pos)})")
    else:
        print("False Negative Rate on 'occluded_trees': N/A (0 positive images in category)")
        
    # Cluttered Multi-Tree FNR
    clut_df = valid_gt_df[(valid_gt_df['category'] == 'cluttered_multi_tree')]
    clut_pos = clut_df[clut_df['ground_truth'] == 'Yes']
    if len(clut_pos) > 0:
        clut_fn = (clut_pos['prediction'] == 'No').sum()
        clut_fnr = clut_fn / len(clut_pos)
        print(f"False Negative Rate on 'cluttered_multi_tree' (GT=Yes): {clut_fnr:.2%} ({clut_fn}/{len(clut_pos)})")
    else:
        print("False Negative Rate on 'cluttered_multi_tree': N/A (0 positive images in category)")
        
    print(f"\n--- AUDIT SUMMARY ---")
    print(f"Row count of data/unmatched_filenames.csv: {len(unmatched_filenames)}")
    print(f"Row count of data/ambiguous_matches.csv: {len(ambiguous_matches)}")
    if len(unmatched_filenames) > 0 or len(ambiguous_matches) > 0:
        resolved_count = len(resolved_mapping)
        print(f"WARNING: Headline accuracy is computed over a subset of matches ({resolved_count} of {len(df)}), not the full set.")
    else:
        print("All 167 CSV rows were successfully resolved to a single candidate image!")
        
    bugs = comp_df[comp_df['status'].isin(['detector_bug_crash', 'detector_unavailable'])]
    if len(bugs) > 0:
        print(f"\n[BUG WARNING] The detector function failed or returned unavailable status for {len(bugs)} images!")
        for _, b_row in bugs.iterrows():
            print(f"  - {b_row['filename']} (status: {b_row['status']})")
    else:
        print("\nNo crashes or unavailable statuses encountered in detect_target_tree().")

def print_breakdowns(sub_df):
    if len(sub_df) == 0:
        print("  No data available for breakdown.")
        return
        
    print("  By Category:")
    categories = sorted(sub_df['category'].dropna().unique())
    for cat in categories:
        cat_df = sub_df[sub_df['category'] == cat]
        total = len(cat_df)
        if total > 0:
            correct = cat_df['match'].sum()
            acc = correct / total
            print(f"    - {cat}: {acc:.2%} ({correct}/{total})")
        else:
            print(f"    - {cat}: N/A (0 images)")
            
    print("  By Confidence (Easy or Hard):")
    confidences = sorted(sub_df['confidence_easy_or_hard'].dropna().unique())
    for conf in confidences:
        conf_df = sub_df[sub_df['confidence_easy_or_hard'] == conf]
        total = len(conf_df)
        if total > 0:
            correct = conf_df['match'].sum()
            acc = correct / total
            print(f"    - {conf}: {acc:.2%} ({correct}/{total})")
        else:
            print(f"    - {conf}: N/A (0 images)")

if __name__ == "__main__":
    main()
