# 데이터 정규화

import pandas as pd
import os


def create_simple_integrated_dataset():
    """
    여러 CSV 파일에서 정규화하여 통합 데이터셋 생성
    """

    # 프로젝트 디렉토리 설정
    project_dir = r"C:\Users\User\PycharmProjects\SilverStats"
    dataset_dir = os.path.join(project_dir, '정규화 데이터셋')

    print("=" * 80)
    print("시도명 정규화 통합 데이터셋 생성")
    print("=" * 80)

    # 통합할 파일 목록
    files = [
        '시도별_65세이상_자살률_정규화.csv',
        '시도별_기초연금_수급률_정규화.csv',
        '시도별_노령화지수_정규화.csv',
        '시도별_독거노인_정규화.csv',
        '시도별_복지시설_정규화.csv'
    ]

    # 각 파일의 존재 여부 확인
    print("\n파일 존재 여부 확인:")
    for file in files:
        file_path = os.path.join(dataset_dir, file)
        exists = os.path.exists(file_path)
        print(f"- {file}: {'존재함' if exists else '존재하지 않음'}")

    # 데이터프레임 저장 리스트
    dataframes = []

    # 시도명 정규화 매핑
    sido_mapping = {
        # 다양한 형태의 시도명을 표준화
        '서울': '서울',
        '서울시': '서울',
        '서울특별시': '서울',
        '부산': '부산',
        '부산시': '부산',
        '부산광역시': '부산',
        '대구': '대구',
        '대구시': '대구',
        '대구광역시': '대구',
        '인천': '인천',
        '인천시': '인천',
        '인천광역시': '인천',
        '광주': '광주',
        '광주시': '광주',
        '광주광역시': '광주',
        '대전': '대전',
        '대전시': '대전',
        '대전광역시': '대전',
        '울산': '울산',
        '울산시': '울산',
        '울산광역시': '울산',
        '세종': '세종',
        '세종시': '세종',
        '세종특별자치시': '세종',
        '경기': '경기',
        '경기도': '경기',
        '강원': '강원',
        '강원도': '강원',
        '강원특별자치도': '강원',
        '충북': '충북',
        '충청북도': '충북',
        '충남': '충남',
        '충청남도': '충남',
        '전북': '전북',
        '전라북도': '전북',
        '전남': '전남',
        '전라남도': '전남',
        '경북': '경북',
        '경상북도': '경북',
        '경남': '경남',
        '경상남도': '경남',
        '제주': '제주',
        '제주도': '제주',
        '제주특별자치도': '제주'
    }

    # 각 파일 로드 및 시도명 정규화
    for file in files:
        file_path = os.path.join(dataset_dir, file)

        if not os.path.exists(file_path):
            print(f"\n경고: {file} 파일이 존재하지 않습니다. 건너뜁니다.")
            continue

        try:
            # 여러 인코딩 시도
            encodings = ['euc-kr', 'cp949', 'utf-8', 'utf-8-sig']
            df = None

            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    print(f"\n{file} 로드 성공 ({encoding} 인코딩)")
                    break
                except Exception as e:
                    continue

            if df is None:
                print(f"{file} 로드 실패. 건너뜁니다.")
                continue

            # 데이터 정보 출력
            print(f"- 행 수: {len(df)}")
            print(f"- 열 수: {len(df.columns)}")
            print(f"- 컬럼: {list(df.columns)}")

            # 시도명 컬럼 찾기
            sido_col = None
            for col in df.columns:
                if '시도' in col or '지역' in col or col in ['시도명', '지역명']:
                    sido_col = col
                    break

            if sido_col is None:
                # 첫 번째 컬럼을 시도명으로 가정
                sido_col = df.columns[0]
                print(f"시도명 컬럼을 찾을 수 없어 첫 번째 컬럼({sido_col})을 사용합니다.")

            # 시도명 정규화
            print(f"시도명 정규화 전: {df[sido_col].unique()}")
            df[sido_col] = df[sido_col].map(lambda x: sido_mapping.get(x, x))
            print(f"시도명 정규화 후: {df[sido_col].unique()}")

            # 시도명 컬럼을 표준화
            df = df.rename(columns={sido_col: '시도명'})

            # 데이터프레임 리스트에 추가
            dataframes.append(df)
            print(f"{file} 처리 완료")

        except Exception as e:
            print(f"{file} 처리 중 오류 발생: {e}")
            continue

    if not dataframes:
        print("\n처리할 데이터가 없습니다.")
        return None

    # 데이터 병합
    print("\n" + "=" * 60)
    print("데이터 병합 시작")
    print("=" * 60)

    # 첫 번째 데이터프레임을 기준으로 시작
    merged_df = dataframes[0]
    print(f"기준 데이터: {files[0]}")

    # 나머지 데이터프레임 병합
    for i, df in enumerate(dataframes[1:], 1):
        before_cols = len(merged_df.columns)
        merged_df = pd.merge(merged_df, df, on='시도명', how='outer')
        after_cols = len(merged_df.columns)
        print(f"{files[i]} 병합 완료 (컬럼 수: {before_cols} → {after_cols})")

    print(f"\n최종 통합 데이터 형태: {merged_df.shape}")
    print(f"최종 컬럼: {list(merged_df.columns)}")

    # 결측값 확인
    print(f"\n결측값 현황:")
    missing_data = merged_df.isnull().sum()
    for col, missing_count in missing_data.items():
        if missing_count > 0:
            print(f"- {col}: {missing_count}개")

    # 데이터 미리보기
    print("\n" + "=" * 60)
    print("통합 데이터셋 미리보기")
    print("=" * 60)
    print(merged_df.to_string(index=False))

    # CSV 파일로 저장
    output_path = os.path.join(dataset_dir, '통합_시도별_데이터셋.csv')
    merged_df.to_csv(output_path, index=False, encoding='euc-kr')
    print(f"\n통합 데이터셋이 '{output_path}'에 저장되었습니다.")

    return merged_df


if __name__ == "__main__":
    result = create_simple_integrated_dataset()