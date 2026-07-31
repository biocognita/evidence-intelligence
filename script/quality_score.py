import math
import pandas as pd
#sample size diminishing return calculation
def sample_size_score(sample_size):
      if pd.isna(sample_size):
            return 0
      if sample_size <= 0:
            return 0
      score=math.log10(sample_size)
      return min(score, 10)
#Scoring of Variables
def calculate_quality_score(study):
    score=0
    if study["Study Type Score"] == 5:
        score+=20
    if study["Study Type Score"] == 4:
            score+=15
    if study["Study Type Score"] == 3:
            score+=10
    if study["Study Type Score"] == 2:
            score+=5
    if study["Study Type Score"] == 1:
            score+=1
    if study["Randomized"] == 1:
        score+=10
    if study["Blinded"] == 1:
        score+=10
    if study["Placebo controlled"] == 3:
        score+= 10
    sample_score = sample_size_score(study["Sample size"])
    score += sample_score
    return score