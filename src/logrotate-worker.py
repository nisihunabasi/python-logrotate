import yaml, sys, os, shutil
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import functions

def main():
    #設定を読み込み。設定ファイルは同じディレクトリにあることを前提とする。
    version = "alpha-20180919"
    #fileHandler = open()

    if len(sys.argv) > 1:
        print("python-logrotate version: " + version)
        if sys.argv[1] == "--help":
            
            sys.exit(0)
        else:
            print("type '--help' to help document.")
            sys.exit(0)

    # 引数未指定で動作。
    fileName = "test.log"
    functions.rotateByTimeInterval("daily", fileName, 3, False, False, False)
    
    #TODO: 2個以上の管理場所に対応
    
    #設定に応じて動作を変える。
    
    

##############################
# 起動スクリプト
##############################

if __name__ == "__main__":
    main()