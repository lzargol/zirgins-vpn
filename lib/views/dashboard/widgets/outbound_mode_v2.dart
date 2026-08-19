import 'package:fl_clash/common/common.dart';
import 'package:fl_clash/enum/enum.dart';
import 'package:fl_clash/providers/providers.dart';
import 'package:fl_clash/state.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class OutboundModeV2 extends ConsumerWidget {
  const OutboundModeV2({super.key});

  void _handleChangeMode(Mode mode) {
    globalState.container.read(setupActionProvider.notifier).changeMode(mode);
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final currentMode = ref.watch(
      patchClashConfigProvider.select((state) => state.mode),
    );

    return Container(
      height: 48,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: const Color(0xFF1B162E),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: const Color(0xFF2E274D), width: 1),
      ),
      child: Row(
        children: [
          Expanded(
            child: _buildPill(
              context: context,
              label: '⚡ Умный',
              isSelected: currentMode == Mode.rule,
              onTap: () => _handleChangeMode(Mode.rule),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _buildPill(
              context: context,
              label: '🌍 Полный',
              isSelected: currentMode == Mode.global,
              onTap: () => _handleChangeMode(Mode.global),
            ),
          ),
          const SizedBox(width: 4),
          Expanded(
            child: _buildPill(
              context: context,
              label: '🚫 Без VPN',
              isSelected: currentMode == Mode.direct,
              onTap: () => _handleChangeMode(Mode.direct),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPill({
    required BuildContext context,
    required String label,
    required bool isSelected,
    required VoidCallback onTap,
  }) {
    return GestureDetector(
      onTap: onTap,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeInOut,
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF5B34B0) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          boxShadow: isSelected
              ? [
                  BoxShadow(
                    color: const Color(0xFF8B5CF6).withOpacity(0.4),
                    blurRadius: 10,
                    offset: const Offset(0, 2),
                  )
                ]
              : null,
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : const Color(0xFF9E98BA),
            fontSize: 13,
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
          ),
        ),
      ),
    );
  }
}
