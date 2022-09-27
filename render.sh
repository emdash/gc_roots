mkdir -p images
input="frames"
output="images"

function frames {
    for file in "${output}"/*
    do
        echo -page 600x400+0+0 "${file}"
    done
}

function render {
    ./roots.py "$1"
    for file in ${input}/*
    do
        dot -T png < "${file}" > "${output}/$(basename ${file}).png"
    done
}

function animate {
    convert -background white \
            -delay 100 \
            -dispose Background \
            -loop 0    \
            -alpha remove \
            $(frames)  \
            output.gif
}

source="$1"
shift

if test -n "$*"
then
    "$@"
else
    render  "${source}"
    animate "$@"
fi
