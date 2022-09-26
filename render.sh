mkdir -p images
input="frames"
output="images"
./roots.py "$1"
for file in ${input}/*
do
    dot -T svg < "${file}" > "${output}/$(basename ${file}).svg"
done
imv-x11 "${output}"
