import os
import apache_log_parser
from pprint import pprint
import datetime
import sqlite3


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


def read_apache_log(log_dir, logformat, dbname):
    """ログファイルを読む関数
    Parameters
    ---------------
    log_dir: str
        ログファイルが存在するディレクトリのパス
    logformat: str
        アクセスログの形式
        
    Return
    ---------
    remote_host_type: set
        リモートホストの種類
    """
    print()
    print('----------ログファイル読み込み開始----------')

    parser = apache_log_parser.make_parser(logformat)
    parsed_log_num = 0
    error_log_num = 0
    remote_host_type = set()

    with sqlite3.connect(dbname) as conn: # データベース作成
        cursor = conn.cursor()

        table = 'apache_logs(remote_host, remote_logname, remote_user, time_received, \
        request_first_line, status, response_bytes_clf, request_header_referer, request_header_user_agent)'
        create_table = 'create table {}'.format(table)
        cursor.execute(create_table) # テーブル作成
        sql = 'insert into {} values(?, ?, ?, ?, ?, ?, ?, ?, ?)'.format(table) # データの追加文のフォーマット作成

        for filename in os.listdir(log_dir):
            log_file = os.path.join(log_dir, filename)
            gen = file_generator(log_file) # ファイルの中身を一行ずつ返すジェネレーター作成
            for line in gen:
                try:
                    parsed_line = parser(line)
                    # データベースに格納
                    apache_log = (
                        parsed_line['remote_host'],
                        parsed_line['remote_logname'],
                        parsed_line['remote_user'],
                        parsed_line['time_received_isoformat'].replace('T', ' '),
                        parsed_line['request_first_line'],
                        parsed_line['status'],
                        parsed_line['response_bytes_clf'],
                        parsed_line['request_header_referer'],
                        parsed_line['request_header_user_agent'],
                    )
                    cursor.execute(sql, apache_log)
                    parsed_log_num += 1
                    remote_host_type.add(parsed_line['remote_host']) # リモートホストの種類を記録
                except ValueError:
                    error_log_num += 1

        print()
        pprint('=== Read Summary ===')
        pprint('Parsed : {}'.format(parsed_log_num))
        pprint('ValueError : {}'.format(error_log_num))
        pprint('====================')
        print()

        conn.commit() # データベースファイルに更新結果を反映
    return remote_host_type


def aggregate_access_count(dbname, remote_host_type, start='', end=''):
    """各時間帯毎（２４通り）のアクセス件数とリモートホスト別のアクセス件数を集計する関数
    Parameters
    ---------------
    dbname: str
        パースされたログを集積したデータベースのパス
    start: str
        集計開始日
    end: str
        集計終了日
        
    Return
    ---------
    access_num_per_hour: list
        各時間帯毎のアクセス件数を格納したリスト
    access_num_per_host: list(tupple)
        ホスト名とそのアクセス件数のタプルをアクセス件数に関して降順に並び替えたリスト
    """
    access_num_per_hour = [0] * 24
    access_num_per_host = dict()
    with sqlite3.connect(dbname) as conn: # データベース接続
        cursor = conn.cursor()
        
        # 期間指定がある場合
        if start != '' and end != '':
            # 時間帯ごとのアクセス件数の集計   
            for i in range(24):
                sql = 'select count(*) from apache_logs where (time(time_received) between "{0:0=2}:00:00" and "{0:0=2}:59:59") \
            and (date(time_received) between "{1}" and "{2}")'.format(i, start, end)
                cursor.execute(sql)
                access_num_per_hour[i] = cursor.fetchone()[0] # 取得した値を取り出す
            # リモートホスト別のアクセス件数の集計
            for remote_host in remote_host_type:
                sql = 'select count(*) from apache_logs where (remote_host = "{0}") and (date(time_received) between "{1}" and "{2}")'.format(remote_host, start, end)
                cursor.execute(sql)
                access_num_per_host[remote_host] = cursor.fetchone()[0]
            
        # 期間指定がない場合    
        else:
            # 時間帯ごとのアクセス件数の集計   
            for i in range(24):
                sql = 'select count(*) from apache_logs where (time(time_received) between "{0:0=2}:00:00" and "{0:0=2}:59:59")'.format(i)
                cursor.execute(sql) # 文を実行
                access_num_per_hour[i] = cursor.fetchone()[0] # 取得した値を取り出す
            # リモートホスト別のアクセス件数の集計
            for remote_host in remote_host_type:
                sql = 'select count(*) from apache_logs where (remote_host = "{}")'.format(remote_host)
                cursor.execute(sql)
                access_num_per_host[remote_host] = cursor.fetchone()[0]
                
        access_num_per_host = sorted(access_num_per_host.items(), key=lambda x:x[0]) # アクセスの多いリモートホストの順にソート
        
    return access_num_per_hour, access_num_per_host


if __name__ == '__main__':
    LOG_FORMAT = '%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
    dbname = 'apache_log.db' # 大規模データに対応するために一時的に格納するデータベース
    try:
        os.remove(dbname) # ctrl + C などで強制終了した時に残ったデータベースを削除しておく
    except FileNotFoundError:
        pass
    remote_host_type = read_apache_log(input('アクセスログディレクトリのパスを入力して下さい．: '), LOG_FORMAT, dbname)
    
    if input('アクセスログの期間指定しますか？ [Y/n]: ').lower() == 'y':
        start = datetime.datetime.strptime(input('「年/月/日」の形式で半角で開始期間を入力して下さい．: '), '%Y/%m/%d')
        end = datetime.datetime.strptime(input('「年/月/日」の形式で半角で終了期間を入力して下さい．: '), '%Y/%m/%d')
        # sqliteで利用可能な形式に変換
        start = '{}-{:0=2}-{:0=2}'.format(start.year, start.month, start.day)
        end = '{}-{:0=2}-{:0=2}'.format(end.year, end.month, end.day)
        access_num_per_hour, access_num_per_host = aggregate_access_count(dbname, remote_host_type, start, end)

    else:
        access_num_per_hour, access_num_per_host = aggregate_access_count(dbname, remote_host_type)

    print()

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
            os.remove(dbname)
            break

        else:
            print('不適切な入力です．再度入力して下さい．')
            print()
            continue