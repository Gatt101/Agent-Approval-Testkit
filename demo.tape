# Record with: vhs demo.tape   (https://github.com/charmbracelet/vhs)
Output demo.gif
Set FontSize 16
Set Width 1200
Set Height 720
Set Theme "Catppuccin Mocha"
Set TypingSpeed 40ms
Set Shell "powershell"

Hide
Type "function prompt { '> ' }; cls"
Enter
Sleep 1s
Show

Type "# A human approved: send_payment(amount=100, to=acct_vendor_123)"
Enter
Sleep 1s
Type "approval-test run examples/vulnerable_payment_agent"
Enter
Sleep 6s
Type "# Fix: bind the whole action by hash + single-use approvals"
Enter
Sleep 1s
Type "approval-test run examples/secure_payment_agent"
Enter
Sleep 8s
