import 'package:fl_clash/common/common.dart';
import 'package:fl_clash/enum/enum.dart';
import 'package:fl_clash/providers/providers.dart';
import 'package:fl_clash/state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class ZirginsStartButton extends ConsumerWidget {
  const ZirginsStartButton({super.key});

  Future<void> _handleToggle(BuildContext context, WidgetRef ref) async {
    final coreStatus = ref.read(coreStatusProvider);
    if (coreStatus == CoreStatus.connecting) return;
    ref.read(coreActionProvider.notifier).toggle();
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isStart = ref.watch(isStartProvider);
    final coreStatus = ref.watch(coreStatusProvider);

    final isConnecting = coreStatus == CoreStatus.connecting;

    return GestureDetector(
      onTap: () => _handleToggle(context, ref),
      child: Container(
        height: 56,
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isStart
                ? [const Color(0xFF6D28D9), const Color(0xFF4F46E5)]
                : [const Color(0xFF5B21B6), const Color(0xFF4338CA)],
          ),
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF7C3AED).withOpacity(isStart ? 0.55 : 0.3),
              blurRadius: 18,
              spreadRadius: isStart ? 3 : 1,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        alignment: Alignment.center,
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (isConnecting)
              const SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: Colors.white,
                ),
              )
            else
              Icon(
                isStart ? Icons.pause : Icons.play_arrow,
                color: Colors.white,
                size: 24,
              ),
            const SizedBox(width: 10),
            Text(
              isStart ? 'ПОДКЛЮЧЕНО' : 'ПОДКЛЮЧИТЬСЯ',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 16,
                fontWeight: FontWeight.w800,
                letterSpacing: 1.2,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
