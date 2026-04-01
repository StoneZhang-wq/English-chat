import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/p2p_models.dart';
import 'p2p_room_screen.dart';

class P2pMatchingScreen extends StatefulWidget {
  final P2pScenarioCard selected;
  const P2pMatchingScreen({super.key, required this.selected});

  @override
  State<P2pMatchingScreen> createState() => _P2pMatchingScreenState();
}

class _P2pMatchingScreenState extends State<P2pMatchingScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _c;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _c = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 2000),
    )..repeat();
    _timer = Timer(const Duration(seconds: 3), () {
      if (!mounted) return;
      Navigator.of(context).pushReplacement(
        MaterialPageRoute<void>(
          builder: (_) => P2pRoomScreen(
            scenario: widget.selected,
            initialSpec: P2pRoleSpec(
              partnerRole: 'Partner',
              yourRole: 'You',
              task: widget.selected.task,
            ),
          ),
        ),
      );
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF151311),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 24),
            Expanded(
              child: Center(
                child: AnimatedBuilder(
                  animation: _c,
                  builder: (context, _) {
                    return CustomPaint(
                      painter: _RadarPainter(t: _c.value),
                      child: SizedBox(
                        width: 220,
                        height: 220,
                        child: Center(
                          child: Container(
                            width: 18,
                            height: 18,
                            decoration: BoxDecoration(
                              color: echoTaskYellow,
                              shape: BoxShape.circle,
                              boxShadow: [
                                BoxShadow(
                                  color: echoTaskYellow.withValues(alpha: 0.35),
                                  blurRadius: 18,
                                ),
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ),
            Text(
              'Finding a partner...',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: Colors.white.withValues(alpha: 0.9),
                    fontFamily: 'serif',
                    fontStyle: FontStyle.italic,
                    fontWeight: FontWeight.w400,
                  ),
            ),
            const SizedBox(height: 8),
            Text(
              'SCENARIO: ${widget.selected.title.toUpperCase()}',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Colors.white.withValues(alpha: 0.55),
                    letterSpacing: 1.1,
                  ),
            ),
            const SizedBox(height: 34),
          ],
        ),
      ),
    );
  }
}

class _RadarPainter extends CustomPainter {
  final double t;
  const _RadarPainter({required this.t});

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final r = math.min(size.width, size.height) / 2;

    final bg = Paint()
      ..color = const Color(0xFF151311)
      ..style = PaintingStyle.fill;
    canvas.drawCircle(center, r, bg);

    final ring = Paint()
      ..color = Colors.white.withValues(alpha: 0.06)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1;

    canvas.drawCircle(center, r * 0.35, ring);
    canvas.drawCircle(center, r * 0.65, ring);
    canvas.drawCircle(center, r * 0.95, ring);

    final sweep = Paint()
      ..shader = SweepGradient(
        colors: [
          echoTaskYellow.withValues(alpha: 0.0),
          echoTaskYellow.withValues(alpha: 0.10),
          echoTaskYellow.withValues(alpha: 0.0),
        ],
        stops: const [0.0, 0.15, 1.0],
        transform: GradientRotation(t * math.pi * 2),
      ).createShader(Rect.fromCircle(center: center, radius: r))
      ..blendMode = BlendMode.plus;

    canvas.drawCircle(center, r, sweep);

    final pulse = (t < 0.5) ? (t / 0.5) : ((1 - t) / 0.5);
    final p = Paint()
      ..color = echoTaskYellow.withValues(alpha: 0.12 * pulse)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2;
    canvas.drawCircle(center, r * (0.2 + 0.6 * t), p);
  }

  @override
  bool shouldRepaint(covariant _RadarPainter oldDelegate) => oldDelegate.t != t;
}

