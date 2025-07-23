<!-- To change time for Automatic scrapping in MacOS -->
nano ~/Library/LaunchAgents/com.bdjobs.scraper.plist   <!-- In Terminal project Repository -->

    <key>StartCalendarInterval</key>    
    <dict>
        <key>Hour</key>
        <integer>22</integer>  <!-- 24-hour format Change the integers-->
        <key>Minute</key>
        <integer>15</integer>
    </dict>

launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.bdjobs.scraper.plist      
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.bdjobs.scraper.plist

launchctl list | grep bdjobs

sudo pmset repeat wakeorpoweron MTWRFSU 04:40:00    <!-- 24-hour format Change the integers-->



