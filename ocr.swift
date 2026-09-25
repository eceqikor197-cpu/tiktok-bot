import Vision
import Foundation
import AppKit

guard CommandLine.arguments.count > 1 else { exit(1) }
let imagePath = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: imagePath),
      let cgImage = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    exit(1)
}

let request = VNRecognizeTextRequest { (request, error) in
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for observation in observations {
        guard let topCandidate = observation.topCandidates(1).first else { continue }
        print(topCandidate.string)
    }
}
request.recognitionLanguages = ["ru-RU", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
