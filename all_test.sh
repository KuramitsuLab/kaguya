#!/bin/bash

TARGET=$1

mkdir test_${TARGET}/

grammars=(
    "gk0"
    "gk1"
    "gk2"
)

for g in "${grammars[@]}" ; do
    python tester.py test/${TARGET}.txt ${g}.tpeg False n

    mv test/result/${TARGET}.txt test_${TARGET}/result_ver_${g}.txt
    mv test/result/${TARGET}_for_compare.txt test_${TARGET}/for_compare_ver_${g}.txt
    cp ${g}.tpeg test_${TARGET}/${g}.tpeg

    mv graph_${TARGET} test_${TARGET}/graph_ver_${g}
    python compare.py test/python_ans-edit.txt test_${TARGET}/for_compare_ver_${g}.txt > test_${TARGET}/diff_${g}.txt
done

