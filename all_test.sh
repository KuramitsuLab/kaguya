#!/bin/bash

TARGET=$1

mkdir test_${TARGET}/

# gakkou.tpeg
python tester.py test/${TARGET}.txt gakkou.tpeg False y

mv test/result/${TARGET}.txt test_${TARGET}/result_ver_gakkou.txt
mv test/result/${TARGET}_for_compare.txt test_${TARGET}/for_compare_ver_gakkou.txt
cp gakkou.tpeg test_${TARGET}/gakkou.tpeg

mv graph_${TARGET} test_${TARGET}/graph_ver_gakkou


# kaguya.tpeg
python tester.py test/${TARGET}.txt kaguya0.tpeg False y

mv test/result/${TARGET}.txt test_${TARGET}/result_ver_kaguya.txt
mv test/result/${TARGET}_for_compare.txt test_${TARGET}/for_compare_ver_kaguya.txt
cp kaguya0.tpeg test_${TARGET}/kaguya0.tpeg

mv graph_${TARGET} test_${TARGET}/graph_ver_kaguya

# kaguya-kai.tpeg
python tester.py test/${TARGET}.txt kaguya0-kai.tpeg False y

mv test/result/${TARGET}.txt test_${TARGET}/result_ver_kaguya-kai.txt
mv test/result/${TARGET}_for_compare.txt test_${TARGET}/for_compare_ver_kaguya-kai.txt
cp kaguya0-kai.tpeg test_${TARGET}/kaguya0-kai.tpeg

mv graph_${TARGET} test_${TARGET}/graph_ver_kaguya-kai
