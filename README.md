# Apache Log Analyzer
This system analyzes the access log of an Apache HTTP server.

## Description
The system is capable of two main types of analysis.
1. This system aggregates the number of accesses for each time period.
2. This system aggregates the number of accesses for each remote host, and sorts the remote hosts in order of the number of accesses.

In addition to this, it also has three extensions.
1. Support for multiple log files
2. Specify the period
3. Support for large scale data

## Demo
![Gif](https://raw.github.com/wiki/kunifu-study/fixpoint/analyze_log.gif)

## Usage
### select logfile directory
```
$ python analyze_apache_log.py
アクセスログディレクトリのパスを入力して下さい．: ./log_dir
```
Argument: The path to the logfile directory you want to use.

### select the term of access log
```
アクセスログの期間指定しますか？ [Y/n]: y
「年/月/日」の形式で半角で開始期間を入力して下さい．: 2017/4/1
「年/月/日」の形式で半角で終了期間を入力して下さい．: 2017/4/30
```

### select function
```
----------機能選択----------
[1]各時間帯毎のアクセス件数を知りたい
[2]アクセスの多いリモートホストの順にアクセス件数の一覧を表示したい
[3]終了
いずれかの番号を入力して下さい．: 1

----------各時間帯毎のアクセス件数表示モード----------
時間帯幅を入力して下さい．（例:３時間毎 → 3）: 3
```

## Requirements
- Python 3.6.4
- apache-log-parser 1.7.0

## Note
If you want to use a virtual environment, 
```
$ source venv/bin/activate
```

Deactivate
```
(venv)$ deactivate
```

## Licence
[MIT](https://github.com/tcnksm/tool/blob/master/LICENCE)

## Author
[Daiki Kou](https://github.com/kunifu)