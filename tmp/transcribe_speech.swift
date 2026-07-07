import Foundation
import Speech

let args = CommandLine.arguments
guard args.count >= 3 else {
    fputs("usage: transcribe_speech <audio-or-video-file> <output-file>\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: args[1])
let outputURL = URL(fileURLWithPath: args[2])
let locale = Locale(identifier: "en-US")

guard let recognizer = SFSpeechRecognizer(locale: locale) else {
    fputs("SFSpeechRecognizer unavailable for en-US\n", stderr)
    exit(3)
}

let sema = DispatchSemaphore(value: 0)
var authStatus: SFSpeechRecognizerAuthorizationStatus = .notDetermined
SFSpeechRecognizer.requestAuthorization { status in
    authStatus = status
    sema.signal()
}
sema.wait()

guard authStatus == .authorized else {
    fputs("Speech recognition not authorized: \(authStatus.rawValue)\n", stderr)
    exit(4)
}

let request = SFSpeechURLRecognitionRequest(url: inputURL)
request.shouldReportPartialResults = false
if #available(macOS 10.15, *) {
    request.requiresOnDeviceRecognition = false
}

let done = DispatchSemaphore(value: 0)
var finalText = ""
var finalError: Error?

let task = recognizer.recognitionTask(with: request) { result, error in
    if let result = result {
        finalText = result.bestTranscription.formattedString
        if result.isFinal {
            done.signal()
        }
    }
    if let error = error {
        finalError = error
        done.signal()
    }
}

let timeout = DispatchTime.now() + .seconds(7200)
if done.wait(timeout: timeout) == .timedOut {
    task.cancel()
    fputs("speech recognition timed out\n", stderr)
    exit(5)
}

if let finalError = finalError, finalText.isEmpty {
    fputs("speech recognition failed: \(finalError.localizedDescription)\n", stderr)
    exit(6)
}

try finalText.write(to: outputURL, atomically: true, encoding: .utf8)
print("wrote \(outputURL.path)")
