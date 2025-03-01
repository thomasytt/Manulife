import pandas as pd

# 自動下載宏利基金數據
manulife_url = "https://raw.githubusercontent.com/thomasytt/Manulife/main/csv%20data%20for%20DS.csv"
data = pd.read_csv(manulife_url)
   
# 保存到data資料夾
data.to_csv('data/manulife_funds.csv', index=False)
print("數據已保存到 data/manulife_funds.csv")