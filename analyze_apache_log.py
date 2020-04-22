import apache_log_parser
from pprint import pprint


def read_apache_log(log_file, logformat):
    """ログファイルを読む関数
    Parameters
    ---------------
    log_file: str
        ログファイルのパス
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
    with open(log_file) as f:
        for line in f:
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
    
    return parsed_logs


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
    for log_data in log_datas:
        access_num_per_hour[log_data['time_received_datetimeobj'].hour] += 1 # 時間帯ごとのアクセス件数の集計

        if log_data['remote_host'] not in access_num_per_host.keys(): # リモートホスト別のアクセス件数の集計
            access_num_per_host[log_data['remote_host']] = 1
        else:
            access_num_per_host[log_data['remote_host']] += 1
    access_num_per_host = sorted(access_num_per_host.items(), key=lambda x:x[0], reverse=True) # アクセスの多いリモートホストの順にソート

    return access_num_per_hour, access_num_per_host


if __name__ == '__main__':
    LogFormat = '%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"'
    log_datas = read_apache_log(input('apache logfile: '), LogFormat)
    access_num_per_hour, access_num_per_host = aggregate_access_count(log_datas)

    print(access_num_per_hour)
    print(access_num_per_host)