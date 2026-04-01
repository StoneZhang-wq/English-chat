import 'dart:typed_data';

Uint8List float32PcmToWavBytes(Float32List samples, int sampleRate) {
  final int16 = ByteData(samples.length * 2);
  for (var i = 0; i < samples.length; i++) {
    final clamped = samples[i].clamp(-1.0, 1.0);
    final v = (clamped * 32767).toInt();
    int16.setInt16(i * 2, v, Endian.little);
  }
  final pcm = int16.buffer.asUint8List();
  return _wavFromPcm16(pcm, sampleRate: sampleRate, channels: 1);
}

Uint8List _wavFromPcm16(
  Uint8List pcm16Bytes, {
  required int sampleRate,
  required int channels,
}) {
  const bitsPerSample = 16;
  final byteRate = sampleRate * channels * (bitsPerSample ~/ 8);
  final blockAlign = channels * (bitsPerSample ~/ 8);
  final dataSize = pcm16Bytes.length;
  final fileSize = 36 + dataSize;

  final header = ByteData(44);
  var o = 0;

  // RIFF
  header.setUint8(o++, 0x52); // R
  header.setUint8(o++, 0x49); // I
  header.setUint8(o++, 0x46); // F
  header.setUint8(o++, 0x46); // F
  header.setUint32(o, fileSize, Endian.little);
  o += 4;
  header.setUint8(o++, 0x57); // W
  header.setUint8(o++, 0x41); // A
  header.setUint8(o++, 0x56); // V
  header.setUint8(o++, 0x45); // E

  // fmt
  header.setUint8(o++, 0x66); // f
  header.setUint8(o++, 0x6D); // m
  header.setUint8(o++, 0x74); // t
  header.setUint8(o++, 0x20); // space
  header.setUint32(o, 16, Endian.little);
  o += 4;
  header.setUint16(o, 1, Endian.little); // PCM
  o += 2;
  header.setUint16(o, channels, Endian.little);
  o += 2;
  header.setUint32(o, sampleRate, Endian.little);
  o += 4;
  header.setUint32(o, byteRate, Endian.little);
  o += 4;
  header.setUint16(o, blockAlign, Endian.little);
  o += 2;
  header.setUint16(o, bitsPerSample, Endian.little);
  o += 2;

  // data
  header.setUint8(o++, 0x64); // d
  header.setUint8(o++, 0x61); // a
  header.setUint8(o++, 0x74); // t
  header.setUint8(o++, 0x61); // a
  header.setUint32(o, dataSize, Endian.little);

  final out = Uint8List(44 + dataSize);
  out.setRange(0, 44, header.buffer.asUint8List());
  out.setRange(44, 44 + dataSize, pcm16Bytes);
  return out;
}

