import Vision
import Foundation
import AppKit

guard CommandLine.arguments.count > 1 else { exit(1) }
let imagePath = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: imagePath),
      let cgImage = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    exit(1)
}

let width = CGFloat(cgImage.width)
let height = CGFloat(cgImage.height)

let request = VNRecognizeTextRequest { (request, error) in
    guard let observations = request.results as? [VNRecognizedTextObservation] else { return }
    for observation in observations {
        guard let topCandidate = observation.topCandidates(1).first else { continue }
        let box = observation.boundingBox
        let x = box.origin.x * width
        let y = (1 - box.origin.y - box.size.height) * height
        let w = box.size.width * width
        let h = box.size.height * height
        print("\(topCandidate.string) | \(Int(x)),\(Int(y)),\(Int(w)),\(Int(h))")
    }
}
request.recognitionLanguages = ["ru-RU", "en-US"]

let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
try? handler.perform([request])
