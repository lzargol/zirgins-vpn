import 'package:fl_clash/common/common.dart';
import 'package:fl_clash/views/views.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SplitTunnelingWidget extends StatelessWidget {
  const SplitTunnelingWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 150,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF171328),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF2B2348), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text(
                'Раздельное\nтуннелирование',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  height: 1.2,
                ),
              ),
              GestureDetector(
                onTap: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => const AccessView(),
                    ),
                  );
                },
                child: Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    color: const Color(0xFF261F42),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(Icons.add, color: Color(0xFFA78BFA), size: 20),
                ),
              ),
            ],
          ),
          const Spacer(),
          SizedBox(
            height: 48,
            child: Stack(
              children: [
                _buildAppIcon(0, Icons.language, Colors.orange),
                _buildAppIcon(28, Icons.chat_bubble, Colors.indigoAccent),
                _buildAppIcon(56, Icons.smart_toy, Colors.teal),
                _buildAppIcon(84, Icons.send, Colors.lightBlue),
                _buildAppIcon(112, Icons.g_mobiledata, Colors.redAccent),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAppIcon(double left, IconData icon, Color color) {
    return Positioned(
      left: left,
      child: Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: color.withOpacity(0.9),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF171328), width: 2.5),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.3),
              blurRadius: 6,
              offset: const Offset(0, 2),
            )
          ],
        ),
        child: Icon(icon, color: Colors.white, size: 22),
      ),
    );
  }
}

class AdblockShieldWidget extends StatefulWidget {
  const AdblockShieldWidget({super.key});

  @override
  State<AdblockShieldWidget> createState() => _AdblockShieldWidgetState();
}

class _AdblockShieldWidgetState extends State<AdblockShieldWidget> {
  bool isAdblockActive = true;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () {
        setState(() {
          isAdblockActive = !isAdblockActive;
        });
      },
      child: Container(
        height: 150,
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFF171328),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isAdblockActive ? const Color(0xFF6D28D9) : const Color(0xFF2B2348),
            width: isAdblockActive ? 1.5 : 1,
          ),
          boxShadow: isAdblockActive
              ? [
                  BoxShadow(
                    color: const Color(0xFF8B5CF6).withOpacity(0.2),
                    blurRadius: 16,
                    spreadRadius: 2,
                  )
                ]
              : null,
        ),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              SizedBox(
                width: 72,
                height: 72,
                child: Image.asset(
                  'assets/images/tiger_shield_embossed.png',
                  fit: BoxFit.contain,
                  errorBuilder: (_, __, ___) => const Icon(
                    Icons.security,
                    size: 54,
                    color: Color(0xFFA78BFA),
                  ),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                isAdblockActive ? '🛡️ AdBlock ON' : 'AdBlock OFF',
                style: TextStyle(
                  color: isAdblockActive ? const Color(0xFFA78BFA) : const Color(0xFF8E88A8),
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class SubscriptionLockWidget extends StatelessWidget {
  const SubscriptionLockWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 140,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: const Color(0xFF171328),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2B2348), width: 1),
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.lock_outline, color: Color(0xFFA78BFA), size: 28),
          SizedBox(height: 8),
          Text(
            'Активно до 01.01.2026',
            style: TextStyle(
              color: Color(0xFF8E88A8),
              fontSize: 10,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}
