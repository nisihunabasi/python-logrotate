#test_worker.py

import unittest
import yaml, sys, os, shutil
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
#tests ディレクトリに置いときたかったのに、Pythonインタプリタの仕様上おけないみたい。
# @see http://d.hatena.ne.jp/chlere/20110618/1308369842
from src import functions

"""
TODO compressの実装。ZIPで圧縮する。

"""
class TestWorker(unittest.TestCase):
    __testDir = 'test_data'
    __fileName = "test.log"
    #存在しないファイルが指定されたらエラーを出す。
    #設定読み込み、設定ファイルの正規性検証。
    def setUp(self):
        #テストログを置くディレクトリを初期化する。
        self.resetTestData()


    ##############################
    # Test Cases
    ##############################

    def test_daily_rotate(self):
        """
        Daily Rotationのテスト。
        また、Monthly Rotationと処理がかぶっている箇所のテストはこちらで行う。
            :param self: 
        """   
        ##############################
        # 最新ファイルをローテーション
        ##############################
        yesterday = date.today() - timedelta(1)
        recentFileFullPath = self.__testDir + os.path.sep + self.__fileName

        self.addRecentFile(recentFileFullPath, "hogehoge")

        #最新ログを日付単位でローテーションする。処理すると、前日分のログという扱いでローテーションされる。
        functions.rotateByTimeInterval("daily", recentFileFullPath, 10, False, False, False)
        #suffixが昨日のデータが有ればOK
        self.assertTrue(os.path.isfile(recentFileFullPath + "-" + yesterday.strftime("%Y-%m-%d")))
        #最新ログの受け皿になるファイルも存在確認
        self.assertTrue(os.path.isfile(recentFileFullPath))

        self.resetTestData()

        ##############################
        # 処理重複時の挙動
        ##############################
        # 2回目以降の処理は重複とみなし、ログのローテーションを行わない。
        self.addRecentFile(recentFileFullPath, "hugahuga")
        functions.rotateByTimeInterval("daily", recentFileFullPath, 10, False, False, False)
        self.assertTrue(os.path.isfile(recentFileFullPath + "-" + yesterday.strftime("%Y-%m-%d")))
        self.addRecentFile(recentFileFullPath, "hagehage")  #1回目のログと違う文字を入れる。この文字が最新ログに残ったままならテストOK。
        functions.rotateByTimeInterval("daily", recentFileFullPath, 10, False, False, False)  #同じ処理を行う。
        recentFileHandler = open(recentFileFullPath, "r")
        self.assertEqual(recentFileHandler.read(), "hagehage")
        recentFileHandler.close()

        ##############################
        # 世代いっぱいになったときの処理
        ##############################
        # 制限いっぱいまでログが溜まったときには、一番古いログファイルを削除して、最新ログのローテーションスペースを確保する。
        # 世代制限が5だった場合、最新ログを含めないで5つ分残す。それ以外は削除。
        # しかし、「それ以降」という表現ができないので、現実では最古世代より一つ前の世代のファイルだけ消すことにする。
        
        startDate = date.today() - timedelta(6) #一昨日(2日前)から6日前まで、5日分のログを用意する。
        endDate = date.today() - timedelta(2)
        self.addRecentFile(recentFileFullPath, "hogehoge")
        #self.addOldDailyFiles(recentFileFullPath, startDate, endDate, "hogehoge")
        self.addOldFilesByInterval("daily", recentFileFullPath, startDate, endDate, "hogehoge")
        
        functions.rotateByTimeInterval("daily", recentFileFullPath, 5, False, False, False)
        # 上記メソッドで生成されたファイルはあるはず。
        self.assertTrue(os.path.isfile(recentFileFullPath + "-" + yesterday.strftime("%Y-%m-%d")))
        # 6日前のログデータは消えてるはず。
        self.assertFalse(os.path.isfile(recentFileFullPath + "-" + startDate.strftime("%Y-%m-%d")))

        ##############################
        # 空ログファイルはローテーションする/しない(ifEmpty)
        ##############################
        self.resetTestData()
        # ifEmpty=False
        self.addRecentFile(recentFileFullPath, "")
        functions.rotateByTimeInterval("daily", recentFileFullPath, 5, False, False, False)  #空ログならローテーションしない。
        self.assertFalse(os.path.isfile(recentFileFullPath + "-" + yesterday.strftime("%Y-%m-%d")))
        self.addRecentFile(recentFileFullPath, "text available.")
        functions.rotateByTimeInterval("daily", recentFileFullPath, 5, False, False, False)  #空ログではないので、ローテーションする。
        self.assertTrue(os.path.isfile(recentFileFullPath + "-" + yesterday.strftime("%Y-%m-%d")))

        # ifEmpty=True
        self.addRecentFile(recentFileFullPath, "")
        functions.rotateByTimeInterval("daily", recentFileFullPath, 5, True, False, False)  #空ログでもローテーションする。
        self.assertTrue(os.path.isfile(recentFileFullPath + "-" + yesterday.strftime("%Y-%m-%d")))

        ##############################
        # ログファイルが存在していないとき、エラーを出す/出さない(missingOk)
        ##############################
        # わざとログファイルを作らない。
        # この場合のエラーってどんなのだ？
        self.resetTestData()
        
        with self.assertRaises(FileNotFoundError):
            functions.rotateByTimeInterval("daily", recentFileFullPath, 5, False, False, False)  #missingOk = False
        
        functions.rotateByTimeInterval("daily", recentFileFullPath, 5, False, True, False)  #missingOk = True
        #missingOk=Tureなら、最新ログファイルが生成されている。
        self.assertTrue(os.path.isfile(recentFileFullPath))

    def test_monthly_rotate(self):
        """
        Monthly Rotationのテスト。
            :param self: 
        """
        ##############################
        # 最新ファイルをローテーション
        ##############################
        lastMonth = date.today() - relativedelta(months=1)
        recentFileFullPath = self.__testDir + os.path.sep + self.__fileName

        self.addRecentFile(recentFileFullPath, "hogehoge")
        functions.rotateByTimeInterval("monthly", recentFileFullPath, 10, False, False, False)
        #suffixが先月のデータがあるか
        self.assertTrue(os.path.isfile(recentFileFullPath + "-" + lastMonth.strftime("%Y-%m")))
        #最新ログの受け皿になるファイルも存在確認
        self.assertTrue(os.path.isfile(recentFileFullPath))

        self.resetTestData()

        ##############################
        # 世代いっぱいになったときの処理
        ##############################
        startMonth = date.today() - relativedelta(months=6)
        endMonth = date.today() - relativedelta(months=2)
        self.addRecentFile(recentFileFullPath, "hogehugahuga")
        self.addOldFilesByInterval("monthly", recentFileFullPath, startMonth, endMonth, "hogehoge")

        functions.rotateByTimeInterval("monthly", recentFileFullPath, 5, False, False, False)
        #startMonthの月のログは消えているはず。
        self.assertFalse(os.path.isfile(recentFileFullPath + "-" + startMonth.strftime("%Y-%m")))
        #最新ログの受け皿になるファイルも存在確認
        self.assertTrue(os.path.isfile(recentFileFullPath))
        # これ以降のテストはtest_daily_rotateと重複するので行わない。


    def test_size_rotate(self):
        """
        Size based Rotationのテスト。
        ログサイズに応じてローテーションする。
            :param self: 
        """   
        recentFileFullPath = self.__testDir + os.path.sep + self.__fileName
        
        #ローテーションテスト。10byteをリミットにしてローテーションする。
        # ログファイルが10byteならローテーションしない。
        self.addRecentFile(recentFileFullPath, "hogehogehg")   #10byte
        functions.rotateBySizeInterval(recentFileFullPath, 5, 10, False, False)
        self.assertTrue(os.path.isfile(recentFileFullPath))
        self.assertFalse(os.path.isfile(recentFileFullPath + "-0"))
        # 11byteはローテーションする。
        self.addRecentFile(recentFileFullPath, "hogehogehga")   #11byte
        functions.rotateBySizeInterval(recentFileFullPath, 5, 10, False, False)
        self.assertTrue(os.path.isfile(recentFileFullPath + "-0"))
        
        #もう一度ローテーションすると、番号が1のファイルが出来上がる。
        self.addRecentFile(recentFileFullPath, "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt")
        functions.rotateBySizeInterval(recentFileFullPath, 5, 10, False, False)
        self.assertTrue(os.path.isfile(recentFileFullPath + "-1"))

        #制限を0byteにしたら、ローテーションしない。
        self.resetTestData()
        self.addRecentFile(recentFileFullPath, "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt")
        functions.rotateBySizeInterval(recentFileFullPath, 5, 0, False, False)
        self.assertFalse(os.path.isfile(recentFileFullPath + "-0"))

        #空ログファイルはローテーションしない。
        self.resetTestData()
        self.addRecentFile(recentFileFullPath, "")
        functions.rotateBySizeInterval(recentFileFullPath, 5, 10, False, False)
        self.assertFalse(os.path.isfile(recentFileFullPath + "-0"))
        
        #上限までローテーションしたら、古いファイルを削除する。
        self.resetTestData()
        self.addRecentFile(recentFileFullPath, "hogehogehugahuga")  # 12byte
        self.addOldFiles(recentFileFullPath, 5, "hugahuga")
        functions.rotateBySizeInterval(recentFileFullPath, 5, 10, False, False)
        # generationの設定により、番号0-4までのログしか残っていないことになる。
        self.assertFalse(os.path.isfile(recentFileFullPath + "-5"))
        self.assertTrue(os.path.isfile(recentFileFullPath + "-4"))

        ##############################
        # ログファイルが存在していないとき、エラーを出す/出さない(missingOk)
        ##############################
        self.resetTestData()

        #最新ログはセットしない。
        
        with self.assertRaises(FileNotFoundError):
            functions.rotateBySizeInterval(recentFileFullPath, 5, 100, False, False)  #missingOk = False
            
        functions.rotateBySizeInterval(recentFileFullPath, 5, 100, True, False)  #missingOk = True
        # コードが正常なら何も起きない。



    ##############################
    # Helper Methods
    ##############################

    def addRecentFile(self, fileName, innerText=""):
        newFile = open(fileName, "w")
        newFile.write(innerText)
        newFile.close()

    def addOldFiles(self, fileName, generationLimit:int, innerText:str=""):
        """
        過去ログを番号単位で作成する。
            :param self: 
            :param fileName: 
            :param generationLimit:int: 
            :param innerText:str="": 
        """   
        for i in range(generationLimit):
            newFile = open(fileName + "-" + str(i), "w")
            newFile.write(innerText)
            newFile.close()
    def addOldFilesByInterval(self, mode, fileName, startDate:date, endDate:date, innerText:str=""):
        """
        過去ログを一定間隔ごとに作成する。
        startDate, endDateの日付を含めて作成する。
            :param self: 
            :param mode: 間隔のモード。daily, monthlyの2つがある。不正な値が指定されたら全てdailyにする。
            :param fileName: 
            :param startDate:date: 
            :param endDate:date: 
            :param innerText:str="": 
        """
        if startDate > endDate:
            raise Exception("endDate must be newer than startDate.")

        pointer = datetime(startDate.year, startDate.month, startDate.day).date()
        if mode == "monthly":
            step = relativedelta(months=1)
            timeFormat = "%Y-%m"
        else:
            step = timedelta(1)
            timeFormat = "%Y-%m-%d"

        while pointer <= endDate:
            newFile = open(fileName + "-" + pointer.strftime(timeFormat), "w")
            newFile.write(innerText)
            newFile.close()
            pointer = pointer + step

    def resetTestData(self):
        shutil.rmtree(self.__testDir)
        os.mkdir(self.__testDir)

if __name__ == "__main__":
    unittest.main()