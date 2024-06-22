import sys
import os
import pandas as pd
from wordcloud import WordCloud
from PIL import Image

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')
sys.path.insert(0, PARENT_DIR)

import kakaotalk_msg_preprocessor

blockMsg = ['사진\n', 'ㅜ', 'ㅠ', 'ㅋ', 'ㅎ', 'ㅗ', '샵검색', 'ㄷ', 'ㅡ', 'ㄹㅇ', '근데', '진짜', 'ㅇ', '해외 종목 정보', '종목정보', '삭제된 메시지입니다.']

file_path_list =[TEST_DIR + "/datasets/KakaoTalk2.txt",
                ]

if __name__ == '__main__':
    for file_path in file_path_list:
        text = ""
        print(f"------------{file_path} test start-------------------")
        file_type = kakaotalk_msg_preprocessor.check_export_file_type(file_path)
        print(file_type)
        
        messages = kakaotalk_msg_preprocessor.parse(file_type, file_path)

        user = {}
        gift_send_user_list = {}
        user_kicked_list = {}
        
        for item in messages:
            if item["type"] == "msg" and (item["text"].find("선물 게임을 시작합니다") > -1 or item["text"].find("선물게임을 시작합니다") > -1 ):
                if gift_send_user_list.get(item["user_name"]) is None:
                    gift_send_user_list[item["user_name"]] = 0
                gift_send_user_list[item["user_name"]] = gift_send_user_list[item["user_name"]] + 1
            if item["type"] == "msg" and item["text"].find("선물에 당첨되었어요") > -1:
                if user.get(item["user_name"]) is None:
                    user[item["user_name"]] = 0
                user[item["user_name"]] = user[item["user_name"]] + 1
            if item["type"] == 'kicked':
                user_kicked_list[item["user_name"]] = 0

            if item["type"] != 'msg':
                continue
            elif item["user_name"] != "팬다 Jr." and item["user_name"].find("드리고") == -1  and item["user_name"].find("𝗗𝗥𝗘𝗔𝗚𝗢") == -1:
                msg = item["text"]
                tempText = msg
                for bm in blockMsg :
                    tempText = tempText.replace(bm, '')
                text += tempText
        # print(user)
        # 총 받은선물 갯수 리스트
        # user = sorted(user.items(),key=lambda item : item[1],reverse=True)
        # aa = 0
        # for item in user:
        #     print(item[0],item[1],"회")
        #     aa = aa+item[1]
        # print(aa)

        # user_kicked_list[item["user_name"]]
        print(user_kicked_list)
        # for item in user_kicked_list:
        #     print(item.replace('\n', ''))

        # gift_send_user_list = sorted(gift_send_user_list.items(),key=lambda item : item[1],reverse=True)
        # aa = 0
        # for item in gift_send_user_list:
        #     print(item[0],item[1],"회")
        #     aa = aa+item[1]
        # print(aa)

        print("채팅 파싱완료 워드클라우드 작업시작")
        # font = 'C:/Windows/Fonts/NanumBarunGothicBold.ttf'
        font = 'E:/programming/python/kaka/NanumBarunGothicBold.ttf'

        wc = WordCloud(font_path=font, background_color="white", width=1920, height=1080)
        # wc = WordCloud(background_color="white", width=600, height=400)
        wc.generate(text)
        wc.to_file("result.png")

        # url_messages = kakaotalk_msg_preprocessor.url_msg_extract(file_type, messages)
        # print(url_messages)

        # input_df = pd.DataFrame.from_dict(url_messages)[['datetime', 'url']]
        # input_df.rename(columns = {'datetime' : 'clip_at'}, inplace = True)
        # print(input_df)