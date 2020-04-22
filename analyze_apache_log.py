import os
import apache_log_parser
from pprint import pprint
import datetime
from datetime import timedelta
import pandas as pd


def file_generator(file):
    """ファイルの中身を１行ずつ返すジェネレーターを作る関数
    Parameters
    -----------
    file: str
        ログファイルのパス
    """
    with open(file, 'r') as f:
        for line in f:
            yield line


def read_apache_log(log_dir, logformat):
    """ログファイルを読む関数
    Parameters
    ---------------
    log_dir: str
        ログファイルが存在するディレクトリのパス
    logformat: str
        アクセスログの形式
        
    Return
    ---------
    parsed_logs: list(dict)
        パースに成功したログのリスト
    """
    print()
    print('----------ログファイル読み込み開始----------')

    parser = apache_log_parser.make_parser(logformat)
    parsed_logs = []
    error_logs = []
    for filename in os.listdir(log_dir):
        log_file = os.path.join(log_dir, filename)
        gen = file_generator(log_file) # ファイルの中身を一行ずつ返すジェネレーター作成
        for line in gen:
            try:
                parsed_line = parser(line)
                parsed_logs.append(parsed_line)
            except ValueError:
                error_logs.append(line)
                
    print()
    pprint('=== Read Summary ===')
    pprint('Parsed : {}'.format(len(parsed_logs)))
    pprint('ValueError : {}'.format(len(error_logs)))
    pprint('====================')
    print()
    
    return pd.DataFrame(parsed_logs)


def aggregate_access_count(log_datas):
    """各時間帯毎（２４通り）のアクセス件数とリモートホスト別のアクセス件数を集計する関数
    Parameters
    ---------------
    log_datas: list(dict)
        パースに成功したログのリスト
        
    Return
    ---------
    access_num_per_hour: list
        各時間帯毎のアクセス件数を格納したリスト
    access_num_per_host: list(tupple)
        ホスト名とそのアクセス件数のタプルをアクセス件数に関して降順に並び替えたリスト
    """
    access_num_per_hour = [0] * 24
    access_num_per_host = dict()
    for log_data in log_datas.itertuples():
        access_num_per_hour[log_data.time_received_datetimeobj.hour] += 1 # 時間帯ごとのアクセス件数の集計

        if log_data.remote_host not in access_num_per_host.keys(): # リモートホスト別のアクセス件数の集計
            access_num_per_host[log_data.remote_host] = 1
        else:
            access_num_per_host[log_data.remote_host] += 1
    access_num_per_host = sorted(access_num_per_host.items(), key=lambda x:x[0]) # アクセスの多いリモートホストの順にソート

    return access_num_per_hour, access_num_per_host


def squeeze_log(log_datas, start, end):
    return log_datas[(start <= log_datas['time_received_datetimeobj']) & (log_datas['time_received_datetimeobj'] < (end + timedelta(days=1)))]


if __name__ == '__main__':
    LogFormat = '%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
    log_datas = read_apache_log(input('アクセスログディレクトリのパスを入力して下さい．: '), LogFormat)
    
    if input('アクセスログの期間指定しますか？ [Y/n]: ').lower() == 'y':
        start = datetime.datetime.strptime(input('「年/月/日」の形式で半角で開始期間を入力して下さい．: '), '%Y/%m/%d')
        end = datetime.datetime.strptime(input('「年/月/日」の形式で半角で終了期間を入力して下さい．: '), '%Y/%m/%d')
        log_datas = squeeze_log(log_datas, start, end)
    print()

    access_num_per_hour, access_num_per_host = aggregate_access_count(log_datas)

    # print(access_num_per_hour)
    # print(access_num_per_host)

    while True:
        print('----------機能選択----------')
        print('[1]各時間帯毎のアクセス件数を知りたい')
        print('[2]アクセスの多いリモートホストの順にアクセス件数の一覧を表示したい')
        print('[3]終了')
        select_num = int(input('いずれかの番号を入力して下さい．: '))
        print()

        if select_num == 1:
            print('----------各時間帯毎のアクセス件数表示モード----------')
            time_range = int(input('時間帯幅を入力して下さい．（例:３時間毎 → 3）: '))
            print()
            if (24 % time_range) != 0:
                print('Error!: 時間帯は24を割り切れる数にして下さい．')
                print()
            elif time_range == 1:
                print('時間帯\tアクセス数')
                print('------------------')
                for i in range(0, len(access_num_per_hour), time_range):
                    print('{}時\t{}回'.format(i, sum(access_num_per_hour[i:i+time_range])))
            else:
                print('時間帯\tアクセス数')
                print('------------------')
                for i in range(0, len(access_num_per_hour), time_range):
                    print('{}~{}時\t{}回'.format(i, i+time_range, sum(access_num_per_hour[i:i+time_range])))
            print()

        elif select_num == 2:
            print('----------リモートホスト毎のアクセス件数表示モード----------')
            print()
            print('ホスト名\tアクセス数')
            print('--------------------------')
            for host in access_num_per_host:
                print('{}\t{}回'.format(host[0], host[1]))
            print()

        elif select_num == 3:
            print('終了します．')
            break

        else:
            print('不適切な入力です．再度入力して下さい．')
            print()
            continue