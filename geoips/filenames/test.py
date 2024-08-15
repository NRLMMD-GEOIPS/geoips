import base_paths as base_paths_new
import base_paths_old
import os

new_paths = base_paths_new.PATHS
old_paths = base_paths_old.PATHS

compare_values = []

for key in old_paths:
    same = False
    print(f"VARIABLE: {key}")
    if old_paths[key] == new_paths[key]:
        print("\tValues are identical.")
        same = True
    if not old_paths[key] == new_paths[key]:
        try:
            if os.path.abspath(old_paths[key]) == os.path.abspath(new_paths[key]):
                same = True
                print("\tAbsolute paths match.")
        except Exception:
            pass
    if same == False:
        print("\tERROR VALUES ARE DIFFERENT")
        print("\tOld Value", old_paths[key])
        print("\tNew Value", new_paths[key])
    compare_values.append(same)

print("\n")
if sum(compare_values) == len(compare_values):
    print("All values same.")
else:
    print("ERROR, VALUES ARE NOT SAME.")
