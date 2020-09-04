# 
# find the nix opencv
# 
venv_folder="./.venv"
venv_python_folder_name="python3.7"

python_from_nix="$(which -a python | grep '/nix/store' | head -1)"
cv2_shared_object_file="$("$python_from_nix" -c "import cv2; print(cv2.__file__)")"
# if the so object doesn't exist, then copy it
if ! [[ -f "$venv_folder/lib/$venv_python_folder_name" ]] 
then
    ls "$venv_folder/lib/$venv_python_folder_name"
    echo "Copying"
    cp "$cv2_shared_object_file" "$venv_folder/lib/$venv_python_folder_name"
fi

# # check if the library dir has been cached
# name_of_check="libstdcpp_so_6_fix"
# which_gcc_to_look_for="gcc-8.3.0"
# location_of_file_cache="./settings/.cache/.$name_of_check.cleanable"
# # if it hasnt
# if ! [[ -f "$location_of_file_cache" ]]; then
#     # make sure the folder exists
#     mkdir -p "$(dirname "$location_of_file_cache")"
    
#     # find the first gcc package with the missing libstdc++.so.6
#     gcc_cpp_lib_path="$(find -L /nix/store/ -name libstdc++.so.6 2>/dev/null | grep -e "$which_gcc_to_look_for-lib/lib" | head -n 1)"
    
    
#     # save the result to a file (because that^ operation takes awhile)
#     echo "$gcc_cpp_lib_path" > "$location_of_file_cache"
    
# fi
# user
# # load the path from the cache
# gcc_cpp_lib_path="$(cat "$location_of_file_cache")"
# # if the file exists (which it should linux)
# if [[ -f "$gcc_cpp_lib_path" ]] 
# then
#     # get the directory
#     gcc_lib_path="$(dirname "$gcc_cpp_lib_path")"
    
#     # update the library variable
#     export LD_LIBRARY_PATH="$gcc_lib_path:$LD_LIBRARY_PATH"
    
#     echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
# fi

# # also add the path to the libgthread-2.0.so.0
# ubtunut_gtk_lib="/user/lib/x86_64-linux-gnu"
# if [[ -d "$ubtunut_gtk_lib" ]]
# then
#     export LD_LIBRARY_PATH="$ubtunut_gtk_lib:$LD_LIBRARY_PATH"
# fi