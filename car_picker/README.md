# Car Picker Quiz

## Prerequisites
- Python 3.9 이상
- 로컬에 자동차 이미지 데이터가 `car_picker/data` 하위에 존재해야 합니다.

## 설치
```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows
pip install -r car_picker/requirements.txt
```

## 실행
```bash
streamlit run car_picker/app.py
```

브라우저가 자동으로 열리며, 총 10문제와 10분 제한의 자동차 퀴즈를 플레이할 수 있습니다.

## 기능 요약
- 3가지 퀴즈 모드 (제조사 / 제조사+모델 / 제조사+모델+연식)
- 문제당 10개의 보기
- 부분 점수 부여
- 썸네일 캐싱 및 데이터 인덱싱으로 빠른 로딩
