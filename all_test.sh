#!/bin/bash

TARGET=$1

mkdir test_${TARGET}/

# gakkou.tpeg
python tester.py test/${TARGET}.txt gakkou.tpeg False y

cp test/result/${TARGET}.txt test_${TARGET}/ver_gakkou.txt
cp gakkou.tpeg test_${TARGET}/gakkou.tpeg

mv graph/${TARGET} test_${TARGET}/graph/ver_gakkou


# kaguya.tpeg
python tester.py test/${TARGET}.txt kaguya0.tpeg False y

cp test/result/${TARGET}.txt test_${TARGET}/ver_kaguya.txt
cp kaguya0.tpeg test_${TARGET}/kaguya0.tpeg

mv graph/${TARGET} test_${TARGET}/graph/ver_kaguya
