
dfmetrics <- read.csv("~/Desktop/asist-data-sharing/2-data-code-analysis/0-data/parser-output/combined_megafile.csv")
dffluency <- read.csv("~/Desktop/asist-data-sharing/2-data-code-analysis/0-data/parser-output/collaborative_fluency_data.csv")

names(dfmetrics)
names(dffluency)

library(tidyverse)
dfmetrics <- dfmetrics %>% 
  mutate(minute = X)

dffluency <- dffluency %>% 
  mutate(team = Team_number,
         trial = Trial_number)

df <- left_join(dfmetrics, dffluency)


df <- df %>% 
  mutate(team_functional_delay = blue_functional_delay + green_functional_delay + red_functional_delay,
         team_idle_time = blue_idle_time + red_idle_time + green_idle_time)

# remove NA teams
df <- df %>% filter(!is.na(team_rmie_mean) == T)

# remove teams without 2 missions
df %>% group_by(team) %>% count(trial) %>% count(team) -> mission_amount
mission_amount <- mission_amount %>% filter(n == 2)
df <- df %>% filter(team %in% mission_amount$team)


# add mission number (1st or 2nd mission)
## make sure you arrange the data first
df <- df %>% arrange(trial) %>% select(minute, time, trial, team, everything())

condstring <- c(rep(1, 17), rep(2, 17))
df$mission <- condstring

df %>% group_by(team) %>% count(mission) %>% count(team) %>% pull(n) %>% table() # should be all 2 -- indicating 2 missions for all teams


df <- df %>% group_by(team, trial) %>% mutate(lagcomms = lag(comms_total_words)) %>% mutate(diffcomms = comms_total_words - lagcomms)
df <- df %>% filter(minute > 3)

df <- df %>% group_by(team, trial) %>% mutate(cumidle = cumsum(concurrent_idle_time),
                                              cumactive = cumsum(concurrent_activity_time),
                                              cumdelay = cumsum(team_functional_delay))

df <- df %>% group_by(team, trial) %>% mutate(cumeffort = cumsum(process_effort_s),
                                              cumskilluse = cumsum(process_skill_use_s),
                                              cumstrategy = cumsum(process_workload_burnt))




cumdf <- df %>% group_by(team) %>% 
  summarize(
    sscore = sum(total_score),
    seffort = sum(process_effort_s),
    sskill = sum(process_skill_use_s),
    sstrategy = sum(process_workload_burnt),
    scommstotal = sum(comms_total_words),
    commsequity = mean(comms_equity),
    team_marking_mean = mean(team_marking_skill_mean),
    team_marking_sd = mean(team_marking_skill_sd),
    team_walking_mean = mean(team_walking_skill_mean),
    team_walking_sd = mean(team_walking_skill_sd),
    team_transporting_mean = mean(team_transporting_skill_mean),
    team_transporting_sd = mean(team_transporting_skill_sd),
    team_rmie_m = mean(team_rmie_mean),
    team_rmie_s = mean(team_rmie_sd),
    team_sbsod_m = mean(team_sbsod_mean),
    team_sbsod_s = mean(team_sbsod_sd),
    team_anxiety_m = mean(team_anxiety_mean),
    team_anxiety_s = mean(team_anxiety_sd),
    team_anger_m = mean(team_anger_mean),
    team_anger_s = mean(team_anger_sd),
    team_gaming_m = mean(team_gaming_experience_mean),
    team_gaming_s = mean(team_gaming_experience_sd),
    team_knowledge_m = mean(team_mission_knowledge_mean),
    team_knowledge_s = mean(team_mission_knowledge_sd),
    team_idle = sum(team_idle_time),
    team_active = sum(concurrent_activity_time),
    team_fdelay = sum(team_functional_delay)
  )


cumdf <- cumdf %>% filter(! team_anger_m == -1)
useteams <- cumdf %>% dplyr::select(team) %>% pull(team)
df <- df %>% filter(team %in% useteams)



write.csv(df, file = "~/Desktop/asist-data-sharing/2-data-code-analysis/0-data/parser-output/parser-output-cleaned/df.csv")
