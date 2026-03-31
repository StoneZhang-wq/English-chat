import 'package:flutter/material.dart';

import '../../../core/theme/echo_theme.dart';
import '../domain/p2p_models.dart';

class P2pRoomScreen extends StatefulWidget {
  final P2pScenarioCard scenario;
  final P2pRoleSpec initialSpec;

  const P2pRoomScreen({
    super.key,
    required this.scenario,
    required this.initialSpec,
  });

  @override
  State<P2pRoomScreen> createState() => _P2pRoomScreenState();
}

class _P2pRoomScreenState extends State<P2pRoomScreen> {
  late P2pRoleSpec _spec = widget.initialSpec;
  bool _isHintOpen = false;

  final DraggableScrollableController _hintSheetController =
      DraggableScrollableController();
  double _hintSheetExtent = 0.0;

  static const double _hintMinExtent = 0.18;
  static const double _hintInitialExtent = 0.30;
  static const double _hintMaxExtent = 0.78;

  bool _isPartnerMain = true;
  Offset _pipOffset = const Offset(0, 0);
  bool _hasInitPipOffset = false;

  void _swapRoles() {
    setState(() {
      _spec = P2pRoleSpec(
        partnerRole: _spec.yourRole,
        yourRole: _spec.partnerRole,
        task: _spec.task,
      );
    });
  }

  Future<void> _openHint() async {
    if (_isHintOpen) return;
    setState(() {
      _isHintOpen = true;
      _hintSheetExtent = _hintInitialExtent;
    });

    await Future<void>.delayed(const Duration(milliseconds: 16));
    if (!mounted) return;
    if (_hintSheetController.isAttached) {
      try {
        await _hintSheetController.animateTo(
          _hintInitialExtent,
          duration: const Duration(milliseconds: 220),
          curve: Curves.easeOut,
        );
      } catch (_) {
        // ignore: controller may detach during rebuilds
      }
    }
  }

  void _closeHint() {
    if (!_isHintOpen) return;
    setState(() {
      _isHintOpen = false;
      _hintSheetExtent = 0.0;
    });
  }

  void _swapMain() {
    setState(() {
      _isPartnerMain = !_isPartnerMain;
    });
  }

  @override
  void dispose() {
    _hintSheetController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF101010),
      body: SafeArea(
        child: Column(
          children: [
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                children: [
                  Text(
                    'PARTNER (${_spec.partnerRole.toUpperCase()})',
                    style: Theme.of(context).textTheme.labelSmall?.copyWith(
                          color: Colors.white.withValues(alpha: 0.70),
                          letterSpacing: 1.0,
                        ),
                  ),
                  const Spacer(),
                  Container(
                    width: 36,
                    height: 36,
                    decoration: const BoxDecoration(
                      color: echoOnBackground,
                      shape: BoxShape.circle,
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      'L',
                      style: Theme.of(context)
                          .textTheme
                          .labelLarge
                          ?.copyWith(color: Colors.white),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Expanded(
              child: Stack(
                children: [
                  LayoutBuilder(builder: (context, c) {
                    final reservedBottom =
                        _isHintOpen ? (c.maxHeight * _hintSheetExtent) : 0.0;
                    final videoW = c.maxWidth;
                    final videoH = (c.maxHeight - reservedBottom).clamp(0.0, double.infinity);

                    final pipWidth = (videoW * 0.30).clamp(120.0, 168.0);
                    final pipHeight = (pipWidth * 16 / 9).clamp(96.0, 140.0);
                    final safeTop = 118.0; // roughly below the role/task card
                    const margin = 12.0;

                    final maxX =
                        (videoW - margin - pipWidth).clamp(0.0, double.infinity);
                    final maxY =
                        (videoH - margin - pipHeight).clamp(0.0, double.infinity);

                    if (!_hasInitPipOffset && maxY > 0) {
                      WidgetsBinding.instance.addPostFrameCallback((_) {
                        if (!mounted || _hasInitPipOffset) return;
                        setState(() {
                          _pipOffset = Offset(maxX, safeTop.clamp(margin, maxY));
                          _hasInitPipOffset = true;
                        });
                      });
                    }

                    return Stack(
                      children: [
                        Positioned.fill(
                          bottom: reservedBottom,
                          child: _MainPipVideoLayout(
                            isPartnerMain: _isPartnerMain,
                            pipOffset: _pipOffset,
                            onPipOffsetChanged: (v) {
                              setState(() {
                                _pipOffset = v;
                              });
                            },
                            onSwapMain: _swapMain,
                          ),
                        ),
                        if (_isHintOpen)
                          Positioned(
                            left: 0,
                            right: 0,
                            bottom: 0,
                            height: c.maxHeight,
                            child: NotificationListener<
                                DraggableScrollableNotification>(
                              onNotification: (n) {
                                setState(() {
                                  _hintSheetExtent = n.extent;
                                });
                                return false;
                              },
                              child: DraggableScrollableSheet(
                                controller: _hintSheetController,
                                minChildSize: _hintMinExtent,
                                initialChildSize: _hintInitialExtent,
                                maxChildSize: _hintMaxExtent,
                                snap: true,
                                snapSizes: const [
                                  _hintMinExtent,
                                  _hintInitialExtent,
                                ],
                                builder: (context, scrollController) {
                                  return _HintSheet(
                                    scrollController: scrollController,
                                    onClose: _closeHint,
                                  );
                                },
                              ),
                            ),
                          ),
                      ],
                    );
                  }),
                  Positioned(
                    left: 12,
                    right: 12,
                    top: 0,
                    child: _RoleTaskCard(
                      yourRole: _spec.yourRole,
                      task: _spec.task,
                      onSwap: _swapRoles,
                      onHint: _openHint,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              child: _BottomControls(
                onMic: () {},
                onHangup: () => Navigator.of(context).maybePop(),
                onVideo: () {},
              ),
            ),
            const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }
}

class _VideoPanel extends StatelessWidget {
  final bool left;
  final String label;
  const _VideoPanel({required this.left, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: left ? const Color(0xFF161616) : const Color(0xFF242424),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Stack(
        children: [
          Align(
            alignment: Alignment.center,
            child: Icon(
              left ? Icons.person : Icons.videocam,
              size: 56,
              color: Colors.white.withValues(alpha: 0.10),
            ),
          ),
          Positioned(
            left: 12,
            bottom: 10,
            child: Text(
              label,
              style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: Colors.white.withValues(alpha: 0.55),
                  ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MainPipVideoLayout extends StatelessWidget {
  final bool isPartnerMain;
  final Offset pipOffset;
  final ValueChanged<Offset> onPipOffsetChanged;
  final VoidCallback onSwapMain;

  const _MainPipVideoLayout({
    required this.isPartnerMain,
    required this.pipOffset,
    required this.onPipOffsetChanged,
    required this.onSwapMain,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(builder: (context, c) {
      final w = c.maxWidth;
      final h = c.maxHeight;

      final pipWidth = (w * 0.30).clamp(120.0, 168.0);
      final pipHeight = (pipWidth * 16 / 9).clamp(96.0, 140.0);

      final safeTop = 118.0; // roughly below the role/task card
      const margin = 12.0;

      final maxX = (w - margin - pipWidth).clamp(0.0, double.infinity);
      final maxY = (h - margin - pipHeight).clamp(0.0, double.infinity);

      final clamped = Offset(
        pipOffset.dx.clamp(margin, maxX),
        pipOffset.dy.clamp(safeTop.clamp(margin, maxY), maxY),
      );

      Widget main = _VideoPanel(
        left: true,
        label: 'Partner is connected',
      );
      Widget pip = _VideoPanel(
        left: false,
        label: 'You',
      );

      if (!isPartnerMain) {
        final t = main;
        main = pip;
        pip = t;
      }

      return Stack(
        children: [
          Positioned.fill(child: main),
          Positioned(
            left: clamped.dx,
            top: clamped.dy,
            width: pipWidth,
            height: pipHeight,
            child: _PipWindow(
              onTap: onSwapMain,
              onDragDelta: (d) {
                final next = Offset(clamped.dx + d.dx, clamped.dy + d.dy);
                onPipOffsetChanged(next);
              },
              child: pip,
            ),
          ),
        ],
      );
    });
  }
}

class _PipWindow extends StatelessWidget {
  final Widget child;
  final VoidCallback onTap;
  final ValueChanged<Offset> onDragDelta;

  const _PipWindow({
    required this.child,
    required this.onTap,
    required this.onDragDelta,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.transparent,
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        onPanUpdate: (d) => onDragDelta(Offset(d.delta.dx, d.delta.dy)),
        child: DecoratedBox(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: Colors.white.withValues(alpha: 0.18)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.35),
                blurRadius: 18,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(16),
            child: child,
          ),
        ),
      ),
    );
  }
}

class _RoleTaskCard extends StatelessWidget {
  final String yourRole;
  final String task;
  final VoidCallback onSwap;
  final VoidCallback onHint;

  const _RoleTaskCard({
    required this.yourRole,
    required this.task,
    required this.onSwap,
    required this.onHint,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'YOUR ROLE',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: echoMuted,
                        letterSpacing: 1.0,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  yourRole,
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontFamily: 'serif',
                        fontStyle: FontStyle.italic,
                        fontWeight: FontWeight.w400,
                      ),
                ),
                const SizedBox(height: 6),
                Text(
                  'YOUR TASK',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        color: echoMuted,
                        letterSpacing: 1.0,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  task,
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: echoOnBackground.withValues(alpha: 0.85),
                      ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Column(
            children: [
              FilledButton.icon(
                onPressed: onSwap,
                icon: const Icon(Icons.swap_horiz, size: 18),
                label: Text(
                  'SWAP ROLES',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                ),
                style: FilledButton.styleFrom(
                  backgroundColor: echoOnBackground,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
              const SizedBox(height: 10),
              FilledButton.icon(
                onPressed: onHint,
                icon: const Icon(Icons.lightbulb, size: 18),
                label: Text(
                  'NEED A HINT?',
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: echoOnBackground,
                      ),
                ),
                style: FilledButton.styleFrom(
                  backgroundColor: echoTaskYellow,
                  foregroundColor: echoOnBackground,
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _BottomControls extends StatelessWidget {
  final VoidCallback onMic;
  final VoidCallback onHangup;
  final VoidCallback onVideo;

  const _BottomControls({
    required this.onMic,
    required this.onHangup,
    required this.onVideo,
  });

  @override
  Widget build(BuildContext context) {
    Widget pill(IconData icon, {required Color bg, required VoidCallback onTap}) {
      return Material(
        color: bg,
        borderRadius: BorderRadius.circular(22),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(22),
          child: SizedBox(
            width: 44,
            height: 44,
            child: Icon(icon, color: Colors.white, size: 20),
          ),
        ),
      );
    }

    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        pill(Icons.mic, bg: const Color(0xFF2A2A2A), onTap: onMic),
        const SizedBox(width: 12),
        pill(Icons.call_end, bg: const Color(0xFFE53935), onTap: onHangup),
        const SizedBox(width: 12),
        pill(Icons.videocam, bg: const Color(0xFF2A2A2A), onTap: onVideo),
      ],
    );
  }
}

class _HintSheet extends StatelessWidget {
  final ScrollController scrollController;
  final VoidCallback onClose;

  const _HintSheet({
    required this.scrollController,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    final hints = <String>[
      'Try: “Could you say that again a bit slower?”',
      'Try: “I think you mean …, right?”',
      'Try: “Let me summarize what I understood.”',
      'Try: “Can you give me an example?”',
      'Try: “That makes sense. My opinion is …”',
    ];

    return Material(
      color: const Color(0xFF0F0F0F),
      elevation: 16,
      borderRadius: const BorderRadius.only(
        topLeft: Radius.circular(18),
        topRight: Radius.circular(18),
      ),
      child: SafeArea(
        top: false,
        child: Column(
          children: [
            const SizedBox(height: 8),
            Container(
              width: 44,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.white.withValues(alpha: 0.25),
                borderRadius: BorderRadius.circular(999),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 10, 12, 8),
              child: Row(
                children: [
                  Text(
                    'Hints',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          color: Colors.white,
                          fontWeight: FontWeight.w700,
                        ),
                  ),
                  const Spacer(),
                  IconButton(
                    onPressed: onClose,
                    icon: const Icon(Icons.close),
                    color: Colors.white.withValues(alpha: 0.85),
                    tooltip: 'Close',
                  ),
                ],
              ),
            ),
            Expanded(
              child: ListView.separated(
                controller: scrollController,
                padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
                itemBuilder: (context, index) {
                  return Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 14,
                      vertical: 12,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.06),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: Colors.white.withValues(alpha: 0.10),
                      ),
                    ),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(
                          Icons.lightbulb_outline,
                          size: 18,
                          color: Colors.amber.withValues(alpha: 0.90),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            hints[index],
                            style:
                                Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      color: Colors.white.withValues(alpha: 0.90),
                                      height: 1.25,
                                    ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Icon(
                          Icons.content_copy,
                          size: 18,
                          color: Colors.white.withValues(alpha: 0.40),
                        ),
                      ],
                    ),
                  );
                },
                separatorBuilder: (_, __) => const SizedBox(height: 10),
                itemCount: hints.length,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

