
        Add-Type -AssemblyName presentationCore
        $mediaPlayer = New-Object system.windows.media.mediaplayer
        $mediaPlayer.open('A:\\Docker\\livestream\\spike_claude\\graham.wav')
        $mediaPlayer.Volume = 1.0
        $mediaPlayer.Play()
        Start-Sleep -s 20
        $mediaPlayer.Stop()
        