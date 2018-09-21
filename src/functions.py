import yaml, sys, os, shutil
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# TODO: 中の容量が0だったらローテーションする/しない。ifempty
# TODO: ファイルが存在しなかったらローテーションしない/エラー出す。missingok
# TODO: ファイルの圧縮する/しない。compress
def advanceGeneration(fileName:str, generationLimit:int):
    """
    ログの世代を一つ進める。
    1が最新世代で、そこからgenerationLimit分のログを保持する。最新ログの保存場所を確保するため、ログの数字をそれぞれ一つづつ進める。
    また、最古世代のファイルは削除する。
        :param fileName:str: 
        :param generationLimit:int: 
    """
    # 最古世代のファイルがあったら、削除する。→削除しなくてもmoveで上書きされるからやらない。
    
    idxs = range(generationLimit - 1)[::-1] #逆順のリストを得る。.reverse()という書き方はできない；ｗ；
    for gen in idxs:
        try:
            f = open(fileName + "-" + str(gen), "r")
            f.close()
            shutil.move(fileName + "-" + str(gen), fileName + "-" + str(gen + 1))
        except FileNotFoundError:
            #ファイルが存在しなかったら、何もしない。つまり、歯抜けがあったらそのままにしておく。
            pass
    return
    
# TODO: 世代を数えて必要なくなったファイルを削除する機能
def trashOldestGeneration(fileName:str, mode:str, generationLimit:int):
    """
    古くなった世代のファイルを削除する。
        :param fileName:str: 
        :param mode:str: 
        :param generationLimit:int: 
    """
    if mode == "daily":
        oldestDate = date.today() - timedelta(generationLimit + 1)
        oldest = oldestDate.strftime("%Y-%m-%d")
    elif mode == "monthly":
        oldestDate = date.today() - relativedelta(months=generationLimit + 1)
        oldest = oldestDate.strftime("%Y-%m")
    else:
        #size
        oldest = generationLimit - 1    #0スタートなのでリミットから1引く。
    try:
        f = open(fileName + "-" + oldest, "r")
        f.close()
        os.unlink(fileName + "-" + oldest)
    except IOError:
        #ファイルが見つからなかったら何もしない。
        pass

    return None

def lotateByTimeInterval(mode:str, fileName:str, generation:int, ifEmpty:bool, missingOk:bool, isCompress:bool):
    """
    日毎にローテーションを行う。
        :param mode:str: ローテーションモード。dailyとmonthlyをサポートしている。不正な文字列を検知したら強制的にdailyにする。
        :param fileName:str: 
        :param generation:int: 保存可能なファイルの数。世代として表す。
        :param ifEmpty:bool: 
        :param missingOk:bool: 
        :param isCompress:bool: 
        :return: void
    """

    #リネーム後に元ファイル名で新規作成。の前にリネーム先の上書き確認する。
    if mode == "monthly":
        previousDate = date.today() - relativedelta(months=1)
        newFileName = fileName + "-" + str(previousDate.strftime("%Y-%m"))
    else:
        # daily
        previousDate = date.today() - timedelta(1)
        newFileName = fileName + "-" + str(previousDate.strftime("%Y-%m-%d"))
    
    try:
        #既に同じ処理がされているかの確認。ローテーション後のファイル名が既に存在していたら何もしない。
        oldLogFile = open(newFileName, "r")
        oldLogFile.close()
    except FileNotFoundError:
        # ファイルがなかったときだけ、move処理を行う。
        shutil.move(fileName, newFileName)

    # 最新ログの受け皿を作る。既にファイルが存在していたら、実質何もしていないことになる。    
    newLogFile = open(fileName, "a")
    newLogFile.close()

    return

def rotateBySizeInterval(fileName:str, generation:int, limit:int, isCompress:bool):
    """
    ログサイズ基準でローテーションする。
        :param fileName:str: ローテーション対象のファイル名。フルパス。
        :param generation:int: 
        :param limit:int: ログサイズのリミット。byte単位で記述する。この値をログサイズが超えたらローテーションする。
        :param isCompress:bool: 
    """
    try:
        fileSize = os.path.getsize(fileName)
        if fileSize > limit:
            #ローテーションする。
            advanceGeneration(fileName, generation)
            shutil.move(fileName, fileName + "-0")
            return
    except OSError:
        #ファイルがなかったら何もしない。
        return