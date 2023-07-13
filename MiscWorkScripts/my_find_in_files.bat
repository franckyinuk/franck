@echo off
set unixUtils=c:\utils
set findExe=%unixUtils%\find.exe

@echo on
%findExe% . -type f -exec %unixUtils%\grep.exe -nH "%1" {} ;
@echo off

REM %findExe% . -type f -iname *.txt -exec grep.exe -nH $1 {} ; | grep.exe -v "\.svn"
