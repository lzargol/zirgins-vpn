import 'dart:math';
import 'package:fl_clash/common/common.dart';
import 'package:fl_clash/models/models.dart';
import 'package:fl_clash/providers/app.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class NetworkSpeedV2 extends ConsumerWidget {
  const NetworkSpeedV2({super.key});

  Traffic _getLastTraffic(List<Traffic> traffics) {
    if (traffics.isEmpty) return const Traffic();
    return traffics.last;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final traffics = ref.watch(trafficsProvider).list;
    final lastTraffic = _getLastTraffic(traffics);

    return Container(
      height: 145,
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
            children: [
              const Icon(Icons.speed, color: Color(0xFFA78BFA), size: 16),
              const SizedBox(width: 4),
              const Text(
                'Скорость',
                style: TextStyle(color: Color(0xFF8E88A8), fontSize: 12),
              ),
              const Spacer(),
              Text(
                lastTraffic.speedText,
                style: const TextStyle(
                  color: Color(0xFFD4CEEE),
                  fontSize: 11,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const Spacer(),
          SizedBox(
            height: 65,
            width: double.infinity,
            child: CustomPaint(
              painter: _SpeedWavePainter(
                speeds: traffics.map((e) => e.speed.toDouble()).toList(),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _SpeedWavePainter extends CustomPainter {
  final List<double> speeds;
  _SpeedWavePainter({required this.speeds});

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = const Color(0xFF8B5CF6)
      ..strokeWidth = 2.5
      ..style = PaintingStyle.stroke;

    final fillPaint = Paint()
      ..shader = LinearGradient(
        begin: Alignment.topCenter,
        end: Alignment.bottomCenter,
        colors: [
          const Color(0xFF8B5CF6).withOpacity(0.35),
          const Color(0xFF8B5CF6).withOpacity(0.0),
        ],
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height))
      ..style = PaintingStyle.fill;

    final path = Path();
    final fillPath = Path();

    if (speeds.isEmpty) {
      path.moveTo(0, size.height - 4);
      path.quadraticBezierTo(size.width * 0.7, size.height - 4, size.width, size.height * 0.2);
    } else {
      final maxSpeed = max(speeds.reduce(max), 1024.0);
      final step = size.width / max(speeds.length - 1, 1);
      path.moveTo(0, size.height - (speeds[0] / maxSpeed * size.height * 0.85));
      for (int i = 1; i < speeds.length; i++) {
        final x = i * step;
        final y = size.height - (speeds[i] / maxSpeed * size.height * 0.85);
        path.lineTo(x, y);
      }
    }

    fillPath.addPath(path, Offset.zero);
    fillPath.lineTo(size.width, size.height);
    fillPath.lineTo(0, size.height);
    fillPath.close();

    canvas.drawPath(fillPath, fillPaint);
    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant _SpeedWavePainter oldDelegate) => true;
}

class TrafficUsageV2 extends ConsumerWidget {
  const TrafficUsageV2({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final totalTraffic = ref.watch(totalTrafficProvider);
    final upTraffic = totalTraffic.up;
    final downTraffic = totalTraffic.down;

    return Container(
      height: 145,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF171328),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF2B2348), width: 1),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.pie_chart_outline, color: Color(0xFFA78BFA), size: 16),
              SizedBox(width: 4),
              Text(
                'Трафик',
                style: TextStyle(color: Color(0xFF8E88A8), fontSize: 12),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              SizedBox(
                width: 46,
                height: 46,
                child: CustomPaint(
                  painter: _DonutChartPainter(
                    up: upTraffic.toDouble(),
                    down: downTraffic.toDouble(),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _legendItem('Загрузка', const Color(0xFFA78BFA)),
                  const SizedBox(height: 4),
                  _legendItem('Скачивание', const Color(0xFF6D28D9)),
                ],
              ),
            ],
          ),
          const Spacer(),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '↑ ${upTraffic.traffic.value} ${upTraffic.traffic.unit}',
                style: const TextStyle(color: Color(0xFFD4CEEE), fontSize: 11),
              ),
              Text(
                '↓ ${downTraffic.traffic.value} ${downTraffic.traffic.unit}',
                style: const TextStyle(color: Color(0xFFD4CEEE), fontSize: 11),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _legendItem(String text, Color color) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(
          text,
          style: const TextStyle(color: Color(0xFF8E88A8), fontSize: 10),
        ),
      ],
    );
  }
}

class _DonutChartPainter extends CustomPainter {
  final double up;
  final double down;
  _DonutChartPainter({required this.up, required this.down});

  @override
  void paint(Canvas canvas, Size size) {
    final total = up + down;
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    final paintUp = Paint()
      ..color = const Color(0xFFA78BFA)
      ..strokeWidth = 6.5
      ..style = PaintingStyle.stroke;

    final paintDown = Paint()
      ..color = const Color(0xFF6D28D9)
      ..strokeWidth = 6.5
      ..style = PaintingStyle.stroke;

    if (total == 0) {
      canvas.drawCircle(center, radius - 4, paintDown);
      return;
    }

    final upSweep = (up / total) * 2 * pi;
    final downSweep = (down / total) * 2 * pi;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius - 4),
      -pi / 2,
      upSweep,
      false,
      paintUp,
    );
    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius - 4),
      -pi / 2 + upSweep,
      downSweep,
      false,
      paintDown,
    );
  }

  @override
  bool shouldRepaint(covariant _DonutChartPainter oldDelegate) => true;
}
