#SingleInstance off




;======================================================================================================================
;======================================================================================================================
; Define the variables below to make sure that the scripts works on your machine

; List all of your playpens, use | as a separator and put a double | behind the one you wish to be the default choice
Playpens = D:\workdir\trunks4|D:\workdir\trunks5||D:\workdir\trunks6|D:\workdir\Branches\version_15|D:\workdir\Branches\version_16|D:\workdir\Branches
;Playpens = E:\SVN\trunks1\Source||E:\SVN\trunks2\Source|E:\SVN\trunks3\Source|E:\SVN\trunks4\Source
LocalPlayPenLocation = D:\SVN
RemoteMatchingPlayPlenLocation = \\cbi6w039\svn\PL1FRNTE0010NB_copies
RemoteMatchingLocalPlayPlenLocation = E:\SVN\PL1FRNTE0010NB_copies
RemoteHost = cbi6w039

; Set the location of MSBuild
;MsbuildLocation = C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe
MsbuildLocation = MSBuild.exe


; Set Visual studio command prompt
;VSPrompt = C:\apps\MVS11\VC\vcvarsall.bat amd64
;VSPrompt = C:\apps\MVS12\Common7\Tools\VsDevCmd.bat
;VSPrompt = C:\apps\MVS14\Common7\Tools\VsDevCmd.bat
; had to make a copy C:\Program Files (x86)\MSBuild\14.0\bin\Microsoft.Build.Tasks.Core.dll to Microsoft.Build.Tasks.v12.0.dll as it was expected by some MS internal script
;VSPrompt = C:\apps\MVS14\VC\vcvarsall.bat amd64
;VSPrompt = "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat" amd64
VSPrompt = "c:\apps\MVS16\Common7\Tools\VsDevCmd.bat" -arch=x64

; Set svn location
TortoiseProcLocation = C:\Program Files\TortoiseSVN\bin\TortoiseProc.exe

; Set the freefile sync location
FreeFileSyncLocation = C:\Program Files\FreeFileSync\FreeFileSync.exe

; Set freefile sync configuration file locations
FreeFileSyncConfigFileLocation = D:\Users\Mesirard\Documents\VTK_FreeFileSync

NumCPUs = 7
;======================================================================================================================
;======================================================================================================================





BuildOptionsDialog()
{
    Global Playpen, Platform, Configuration, DoBuild, DoCleanUp, DoRebuild, Playpens, DoSourceUpdate, DebugOnly, Revision, RunTests, RunDistributedTests

    Gui, +LastFound
    GuiHWND := WinExist()           ;--get handle to this gui..
    Gui, add, Text, x10, What do you want to update/build?
    Gui, add, Text,, 
    Gui, add, Text, x10 y32 w100, Pick a playpen
    Gui, Add, Checkbox, y+13 wp vDoSourceUpdate Checked, Update source?
    Gui, Add, Checkbox, y+13 wp vDoBuild Checked, Build source?
    Gui, add, Text, y+13 wp, Platform
    Gui, add, Text, y+13 wp, Configuration
    Gui, Add, Checkbox, y+13 wp vDoCleanUp, Clean Up only?

    Gui, add, DropDownList, x+10 y30 w350 vPlaypen, %Playpens%
    Gui, add, Edit, y+5 vRevision, HEAD
    Gui, add, Text, ,
    Gui, Add, DropDownList, y+5 vPlatform, Win32|x64||
    Gui, Add, DropDownList, y+5 vConfiguration, Debug||Release|ReleaseWithVTKDEB|Profile

    Gui, Add, Checkbox, x10  w80 vDoRebuild, Force fresh build?
    Gui, Add, Checkbox, vSynchroniseCode, Synchronise all with Cambridge?
    Gui, Add, Checkbox, vSynchroniseExeOnly, Synchronise Executables only?
    ;Gui, Add, Checkbox, vRunTests, Run faster_test?
    Gui, Add, Checkbox, vRunDistributedTests, Run distributed testing?
    Gui, Add, Button, Default, Go
    Gui, add, Text, , 
    Gui, add, Checkbox, vDebugOnly, Show comands only, don't do anything
    Gui, show, , Update/Build VTK
    
    WinWaitClose, ahk_id %GuiHWND%  ;--waiting for gui to close
    return ClosedWell

    ButtonGo:
        ClosedWell := 0
        Gui, Submit
        Gui, Destroy
    return

    GuiEscape:
    GuiClose:
        ClosedWell := -1
        Gui, Destroy
    return
}

RunWaitOrShowCommand(command, path)
{
    Global DebugOnly

    if (DebugOnly = 1)
    {
        MsgBox, %path% : %command%
    }
    else
    {
        RunWait, %command%, %path%
    }
}

CreateExcludeFileList(path)
{
    IfExist, %path%
        return
        
    FileAppend, thumbs.db`n, %path%
    FileAppend, .pdb`n, %path%
    FileAppend, .lib`n, %path%
    FileAppend, .ilk`n, %path%
    FileAppend, .exp`n, %path%
    FileAppend, .iobj`n, %path%
    FileAppend, .ipdb`n, %path%
    FileAppend, \DistributedTesting\RunData\`n, %path%
    FileAppend, \DistributedTesting\RunData_1\`n, %path%
    FileAppend, distributedlogger.txt`n, %path%
    FileAppend, allTestNames.xml`n, %path%
    FileAppend, \DistributedTesting\Local_TestMachineList.txt`n, %path%
}

Main()
{
    ; Create global variables that will be set by the dialog box
    Global MsbuildLocation, VSPrompt, TortoiseProcLocation, Playpen, Platform, Configuration, DoBuild, DoCleanUp, DoRebuild, Playpens, DoSourceUpdate, DebugOnly, Revision, RunTests, NumCPUs, FreeFileSyncConfigFileLocation, FreeFileSyncLocation, SynchroniseCode, SynchroniseExeOnly, RemoteMatchingPlayPlenLocation, RunDistributedTests, RemoteHost, LocalPlayPenLocation, RemoteMatchingLocalPlayPlenLocation
    ClosedWell := BuildOptionsDialog()
    
	startTime := A_TickCount
	resultString = 
		
    ; values to be used when debugging
    if (1 == 2)
    {
        DoSourceUpdate = 0
        DoCleanUp = 0
        DoBuild = 0
        SynchroniseCode = 0
        RunDistributedTests = 1
        DebugOnly = 0
    }
    
    if (ClosedWell = -1)
    {
        return -1
    }

    sourceFolder = %Playpen%\Source
    if (IsPLaypenABranch(Playpen) == 1)
    {
     sourceFolder = %Playpen%
    }   
    
    endMessageDisplayed = 0
    
    if (DoSourceUpdate)
    {
        path = "."
        UpdateCommand = %TortoiseProcLocation% /command:update /path:%path% /closeonend:2 /rev:%Revision%    
        RunWaitOrShowCommand(UpdateCommand, Playpen)
    }
    
    if (DoCleanUp = 1)
    {
        clean_command = %MsbuildLocation% Blackjack.sln /p:Configuration=%Configuration% /p:Platform=%Platform% /m:%NumCPUs% /t:Clean
        command = %comspec% /k echo command running %clean_command% && %VSPrompt% & %clean_command%
        RunWaitOrShowCommand(command, sourceFolder)
    }
    else if (DoBuild = 1)
    {
		startTimeLocal := A_TickCount

        ; Clean up the builds
        if (DoRebuild = 1)
        {
            clean_command = %MsbuildLocation% Blackjack.sln /p:Configuration=%Configuration% /p:Platform=%Platform% /m:%NumCPUs% /t:Clean && if errorlevel 0 exit
            command = %comspec% /k echo command running %build_command% && %VSPrompt% & %clean_command%
            RunWaitOrShowCommand(command, sourceFolder)
        }

        ; Run the build
        build_command = %MsbuildLocation% Blackjack.sln /p:Configuration=%Configuration% /p:Platform=%Platform% /m:%NumCPUs%
        command = %comspec% /k "echo command running %build_command% && %VSPrompt% & %build_command%"
        
        ; Tweak the command to close if no error happened
            command = %command%  && if errorlevel 0 exit
        
        RunWaitOrShowCommand(command, sourceFolder)
        
        if (RunTests = 1)
        {
            Command = %comspec% /k ..\scripts\python_scripts\bin\faster_test.exe
            Separator = \
            conappPathExtension = 
            if (Platform == "x64")
            {
                conappPathExtension = 64
            }
            RunWaitOrShowCommand(Command, sourceFolder . Separator . Configuration . conappPathExtension)
        }
		
		ellapsedTimeLocal := ConvertMillSecondsToHumanTime(A_TickCount - startTimeLocal)
		resultString = %resultString% `n%ellapsedTimeLocal%, Builds
    }
    
        StringSplit, StringArray, Playpen , \
    index = % StringArray0
    remoteSourceFolder = 
            trunksName = % StringArray%index%
    if (IsPLaypenABranch(Playpen) == 0)
    {
        remoteSourceFolder = %trunksName%\Source
    }
    else
    {
        remoteSourceFolder = %trunksName%
    }
    platformExtension = 
    if (Platform == "x64")
    {
        platformExtension = 64
    }
    conAppFolder = %Configuration%%platformExtension%
            
    if (SynchroniseCode == 1 or SynchroniseExeOnly == 1)
            {
        ; prepare the mapping from x64 and Win32 to the associated folder extension
		startTimeLocal := A_TickCount
        
        dirs := Object()   

        if (SynchroniseExeOnly == 1) 
        {
            dirs.Insert("Debug64")
            dirs.Insert("Release64")
        }
        else 
        {
            dirs.Insert("Debug64")
            dirs.Insert("Release64")
            dirs.Insert("TestData")

            
            ; we sync more stuff for trunks than branches
            if (IsPLaypenABranch(Playpen) == 0)
            {
                dirs.Insert("..\PartData")
                dirs.Insert("..\Tools\DistributedTesting")
            }
        }

        if (1 == 0)
        {
        ; Use XCopy to sync
            excludeFileList = D:\Users\mesirard\Documents\Perso\Siemens\exclude_files.txt
            CreateExcludeFileList(excludeFileList)
            
            for index, element in dirs
            {
                Command = C:\Windows\System32\xcopy "%sourceFolder%\%element%" "%RemoteMatchingPlayPlenLocation%\%remoteSourceFolder%\%element%" /D /I /E /F /Y /H /R /EXCLUDE:%excludeFileList%
                RunWaitOrShowCommand(Command, sourceFolder)                
            }
        }
        else
        {
            ; Use FreeFileSync to sync
            ; make up the list of folders to sync
            foldersToSync = 
            for index, element in dirs
            {
                foldersToSync = %foldersToSync% -leftdir "%sourceFolder%\%element%" -rightdir "%RemoteMatchingPlayPlenLocation%\%remoteSourceFolder%\%element%"
            }
            
            ;MsgBox, trunks selected : %trunksName%
            Command = %FreeFileSyncLocation% "%FreeFileSyncConfigFileLocation%\generic.ffs_batch" %foldersToSync%
            RunWaitOrShowCommand(Command, sourceFolder)                
        }

		ellapsedTimeLocal := ConvertMillSecondsToHumanTime(A_TickCount - startTimeLocal)
		resultString = %resultString% `n%ellapsedTimeLocal%, Synch

    }
    
    if (RunDistributedTests == 1)
    {
		startTimeLocal := A_TickCount
        FormatTime, timeStamp, , yyyy-MM-dd_hh-mm-ss 
        failingTestBatch = failing_test_from_%RemoteHost%_%timeStamp%.xml
        
        startPosition := InStr(sourceFolder, LocalPlayPenLocation)
        endPosition := StrLen(LocalPlayPenLocation)
        endPosition += %startPosition%
        endPosition += 1
        localPathOfPLaypen := SubStr(sourceFolder, endPosition)
        remotePathPlaypen = %RemoteMatchingLocalPlayPlenLocation%\%localPathOfPLaypen%
        remoteDistributedTesterLocation = %remotePathPlaypen%\..\Tools\DistributedTesting\Executables      
        
        ;Command = psexec \\%RemoteHost% -w "%remoteDistributedTesterLocation%" cmd /C "%remoteDistributedTesterLocation%\DistributedTestingApp.exe" -runUnsupervised=%failingTestBatch% -closeWhenFinished
        ; Command = psexec \\%RemoteHost% -i 0 cmd /C "%remoteDistributedTesterLocation%\DistributedTestingApp.exe" -runUnsupervised=%failingTestBatch% -closeWhenFinished
        Command = psexec \\%RemoteHost% -i 0 "%remoteDistributedTesterLocation%\DistributedTestingApp.exe" -runUnsupervised=%failingTestBatch% -closeWhenFinished
        RunWaitOrShowCommand(Command, sourceFolder)        

        resultFile = %RemoteMatchingPlayPlenLocation%\%remoteSourceFolder%\%conAppFolder%\DistributedTesting\%failingTestBatch%
        
		; Open the location of file with the failing tests
		Command = C:\Windows\SysWOW64\explorer.exe "%resultFile%"
		RunWaitOrShowCommand(Command, sourceFolder)

		; Copy the file locally
        destination = C:\Temp
        ;Command = C:\Windows\System32\xcopy "%resultFile%" %destination% /Y
        Command = C:\Windows\SysWOW64\Robocopy.exe "%resultFile%" %destination%
        RunWaitOrShowCommand(Command, sourceFolder)  

		; Open the location of copy
		Command = C:\Windows\SysWOW64\explorer.exe "%destination%"
		RunWaitOrShowCommand(Command, sourceFolder)

		ellapsedTimeLocal := ConvertMillSecondsToHumanTime(A_TickCount - startTimeLocal)
		resultString = %resultString% `n%ellapsedTimeLocal%, Distributed testing, results in %destination%
    }
    
	ellapsedTime := ConvertMillSecondsToHumanTime(A_TickCount - startTime)
	resultString = %resultString% `nTotal run time %ellapsedTime%
	
    if (endMessageDisplayed == 0)
    {
        endMessageDisplayed = 1
        MsgBox, Task completed for %trunksName%, `n %resultString%
    }
    
    return 0   
}

ConvertMillSecondsToHumanTime(timeInMilliSec)
{
	timeInSeconds := Floor(timeInMilliSec / 1000)
	hours := Floor(timeInSeconds / 3600)
	minutes := Mod(Floor(timeInSeconds / 60), 60)
	seconds := Mod(timeInSeconds, 60)
	mSeconds := Mod(timeInMilliSec, 1000)
	string = ""
	if (hours > 1)
	{
		string = %hours%h %minutes%m
	}
	else if (minutes > 1)
	{
		string = %minutes%m %seconds%s 
        }
	else
	{
	string = %seconds%.%mSeconds%s
    }
    
	;MsgBox, converted %timeInMilliSec% to %string%
	
	return string
}

IsPLaypenABranch(playpen)
{
    StringSplit, StringArray, Playpen , \
    index = % StringArray0 - 1
    if (index > 0)
    {
        trunksName = % StringArray%index%
        if (trunksName == "Branches")
        {
            return 1
        }
    }
    return 0   
}


Main()
ExitApp

