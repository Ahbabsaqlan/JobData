<!-- To change time for Automatic scrapping in MacOS -->
nano ~/Library/LaunchAgents/com.bdjobs.scraper.plist   <!-- In Terminal project Repository -->

    <?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bdjobs.scraper</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/jihan/JobData/run_job.sh</string>
    </array>

    <!-- Runs daily at 4:45 AM -->
    <key>StartCalendarInterval</key>    
    <dict>
        <key>Hour</key>
        <integer>22</integer>  <!-- 24-hour format Change the integers-->
        <key>Minute</key>
        <integer>15</integer>
    </dict>

    <!-- Wake Mac if sleeping -->
    <key>WakeOnDemand</key>
    <true/>

    <!-- Where launchd will log stdout/stderr -->
    <key>StandardOutPath</key>
    <string>/Users/jihan/JobData/launchd_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/jihan/JobData/launchd_stderr.log</string>
</dict>
</plist>


launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.bdjobs.scraper.plist      
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.bdjobs.scraper.plist

launchctl list | grep bdjobs

sudo pmset repeat wakeorpoweron MTWRFSU 04:40:00    <!-- 24-hour format Change the integers-->



