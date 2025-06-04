import pandas as pd
import os


def clean_integrated_dataset():
    """
    통합 데이터셋에서 불필요한 컬럼들을 제거하는 함수
    """

    # 프로젝트 디렉토리 설정
    project_dir = r"C:\Users\User\PycharmProjects\SilverStats"
    dataset_dir = os.path.join(project_dir, '데이터셋')

    # 파일 경로
    input_file = os.path.join(dataset_dir, '통합_시도별_고령화_데이터셋_v2.csv')

    print(f"입력 파일: {input_file}")
    print(f"파일 존재 여부: {os.path.exists(input_file)}")

    # 제거할 컬럼 목록
    columns_to_remove = [
        '총수급자수',
        '전체일반가구',
        '65세이상_총자살자수'
    ]

    print(f"\n제거할 컬럼: {columns_to_remove}")

    try:
        # 데이터 로드
        encodings = ['euc-kr', 'cp949', 'utf-8', 'utf-8-sig']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(input_file, encoding=encoding)
                print(f"데이터 로드 성공 ({encoding} 인코딩)")
                break
            except Exception as e:
                print(f"{encoding} 인코딩 시도 실패: {str(e)[:100]}...")

        if df is None:
            print("데이터 로드 실패")
            return None

        # 원본 데이터 정보
        print(f"\n원본 데이터 정보:")
        print(f"- 행 수: {len(df)}")
        print(f"- 열 수: {len(df.columns)}")
        print(f"- 컬럼: {list(df.columns)}")

        # 제거할 컬럼이 실제로 존재하는지 확인
        existing_columns_to_remove = []
        missing_columns = []

        for col in columns_to_remove:
            if col in df.columns:
                existing_columns_to_remove.append(col)
            else:
                missing_columns.append(col)

        if existing_columns_to_remove:
            print(f"\n실제로 제거될 컬럼: {existing_columns_to_remove}")

        if missing_columns:
            print(f"존재하지 않는 컬럼: {missing_columns}")

        # 컬럼 제거
        if existing_columns_to_remove:
            df_cleaned = df.drop(columns=existing_columns_to_remove)
            print(f"\n컬럼 제거 완료!")
        else:
            df_cleaned = df.copy()
            print(f"\n제거할 컬럼이 없어서 원본 데이터를 유지합니다.")

        # 정리된 데이터 정보
        print(f"\n정리된 데이터 정보:")
        print(f"- 행 수: {len(df_cleaned)}")
        print(f"- 열 수: {len(df_cleaned.columns)}")
        print(f"- 컬럼: {list(df_cleaned.columns)}")

        # 데이터 미리보기
        print(f"\n정리된 데이터 미리보기:")
        print("=" * 80)
        print(df_cleaned.to_string(index=False))

        # 결측값 확인
        missing_values = df_cleaned.isnull().sum()
        print(f"\n결측값 현황:")
        for col, count in missing_values.items():
            if count > 0:
                print(f"- {col}: {count}개")
            else:
                print(f"- {col}: 결측값 없음")

        # 정리된 데이터셋 저장
        output_path = os.path.join(dataset_dir, '통합_시도별_고령화_데이터셋_최종.csv')
        df_cleaned.to_csv(output_path, index=False, encoding='euc-kr')
        print(f"\n정리된 통합 데이터셋이 '{output_path}'에 저장되었습니다.")

        # 데이터 요약 통계
        print(f"\n" + "=" * 60)
        print("데이터 요약 통계")
        print("=" * 60)

        numeric_cols = df_cleaned.select_dtypes(include=['float64', 'int64']).columns
        if len(numeric_cols) > 0:
            summary_stats = df_cleaned[numeric_cols].describe()
            print(summary_stats.round(2))

        # 상관관계 매트릭스 (수치형 컬럼만)
        if len(numeric_cols) > 1:
            print(f"\n" + "=" * 60)
            print("주요 지표 간 상관관계")
            print("=" * 60)

            corr_matrix = df_cleaned[numeric_cols].corr()

            # 자살률과 다른 지표들의 상관관계
            if '65세이상_평균자살률' in corr_matrix.columns:
                suicide_corr = corr_matrix['65세이상_평균자살률'].sort_values(key=abs, ascending=False)
                print(f"\n65세 이상 평균자살률과 다른 지표 간의 상관관계:")
                for idx, corr in suicide_corr.items():
                    if idx != '65세이상_평균자살률':
                        correlation_strength = ""
                        if abs(corr) >= 0.7:
                            correlation_strength = " (강한 상관관계)"
                        elif abs(corr) >= 0.5:
                            correlation_strength = " (중간 상관관계)"
                        elif abs(corr) >= 0.3:
                            correlation_strength = " (약한 상관관계)"
                        else:
                            correlation_strength = " (매우 약한 상관관계)"

                        print(f"- {idx}: {corr:.3f}{correlation_strength}")

            # 노령화지수와 다른 지표들의 상관관계
            if '평균노령화지수' in corr_matrix.columns:
                aging_corr = corr_matrix['평균노령화지수'].sort_values(key=abs, ascending=False)
                print(f"\n평균노령화지수와 다른 지표 간의 상관관계:")
                for idx, corr in aging_corr.items():
                    if idx != '평균노령화지수':
                        correlation_strength = ""
                        if abs(corr) >= 0.7:
                            correlation_strength = " (강한 상관관계)"
                        elif abs(corr) >= 0.5:
                            correlation_strength = " (중간 상관관계)"
                        elif abs(corr) >= 0.3:
                            correlation_strength = " (약한 상관관계)"
                        else:
                            correlation_strength = " (매우 약한 상관관계)"

                        print(f"- {idx}: {corr:.3f}{correlation_strength}")

        # 시도별 종합 순위 계산
        print(f"\n" + "=" * 60)
        print("시도별 고령화 종합 지수")
        print("=" * 60)

        # 정규화를 위한 지표별 순위 계산
        ranking_cols = []
        for col in numeric_cols:
            if col != '시도명':
                ranking_cols.append(col)

        if ranking_cols:
            df_rank = df_cleaned.copy()

            # 각 지표를 0-1 사이로 정규화 (높을수록 고령화 심각)
            for col in ranking_cols:
                if col in ['65세이상_평균자살률', '평균노령화지수']:
                    # 높을수록 나쁨 (그대로)
                    df_rank[f'{col}_정규화'] = (df_rank[col] - df_rank[col].min()) / (
                                df_rank[col].max() - df_rank[col].min())
                elif col in ['기초연금수급률', '독거노인비율']:
                    # 높을수록 나쁨 (그대로)
                    df_rank[f'{col}_정규화'] = (df_rank[col] - df_rank[col].min()) / (
                                df_rank[col].max() - df_rank[col].min())
                elif col in ['복지시설밀도']:
                    # 높을수록 좋음 (역순)
                    df_rank[f'{col}_정규화'] = 1 - (df_rank[col] - df_rank[col].min()) / (
                                df_rank[col].max() - df_rank[col].min())

            # 종합 지수 계산 (정규화된 값들의 평균)
            normalized_cols = [col for col in df_rank.columns if '_정규화' in col]
            if normalized_cols:
                df_rank['고령화종합지수'] = df_rank[normalized_cols].mean(axis=1)

                # 종합 지수 기준으로 정렬
                df_rank = df_rank.sort_values('고령화종합지수', ascending=False)

                print("시도별 고령화 종합 지수 (1.0에 가까울수록 고령화 심각):")
                for _, row in df_rank.iterrows():
                    print(f"{row['시도명']:8s}: {row['고령화종합지수']:.3f}")

        return df_cleaned

    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = clean_integrated_dataset()
