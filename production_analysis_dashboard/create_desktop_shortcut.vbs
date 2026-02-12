Set WshShell = CreateObject("WScript.Shell")
Set oShellLink = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") & "\생산분석 대시보드.lnk")
oShellLink.TargetPath = WshShell.CurrentDirectory & "\start_dashboard_advanced.bat"
oShellLink.WorkingDirectory = WshShell.CurrentDirectory
oShellLink.WindowStyle = 1
oShellLink.IconLocation = "C:\Windows\System32\shell32.dll,23"
oShellLink.Description = "Production Analysis Dashboard v2.1.1"
oShellLink.Save

MsgBox "바탕화면에 바로가기가 생성되었습니다!" & vbCrLf & vbCrLf & "파일명: 생산분석 대시보드.lnk", vbInformation, "바로가기 생성 완료"
