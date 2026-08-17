import 'dart:math';

import 'package:fl_clash/common/common.dart';
import 'package:fl_clash/enum/enum.dart';
import 'package:fl_clash/providers/providers.dart';
import 'package:fl_clash/state.dart';
import 'package:fl_clash/widgets/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

class OutboundMode extends StatelessWidget {
  const OutboundMode({super.key});

  void _handleChangeMode(Mode mode) {
    globalState.container.read(setupActionProvider.notifier).changeMode(mode);
  }

  @override
  Widget build(BuildContext context) {
    final appLocalizations = context.appLocalizations;
    final height = getWidgetHeight(2);
    return SizedBox(
      height: height,
      child: Consumer(
        builder: (_, ref, _) {
          final mode = ref.watch(
            patchClashConfigProvider.select((state) => state.mode),
          );
          return Theme(
            data: Theme.of(context).copyWith(
              splashColor: Colors.transparent,
              highlightColor: Colors.transparent,
              hoverColor: Colors.transparent,
            ),
            child: CommonCard(
              onPressed: () {},
              info: Info(
                label: appLocalizations.outboundMode,
                iconData: Icons.call_split_sharp,
              ),
              child: Padding(
                padding: const EdgeInsets.only(top: 12, bottom: 12),
                child: RadioGroup<Mode>(
                  groupValue: mode,
                  onChanged: (value) {
                    if (value == null) {
                      return;
                    }
                    _handleChangeMode(value);
                  },
                  child: LayoutBuilder(
                    builder: (_, constraints) {
                      final maxHeight = constraints.maxHeight;
                      return Column(
                        mainAxisSize: MainAxisSize.max,
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.start,
                        children: [
                          for (final item in Mode.values)
                            ListItem.radio(
                              horizontalTitleGap: 8,
                              tileTitleAlignment: ListTileTitleAlignment.center,
                              minTileHeight: min(
                                maxHeight / 3,
                                globalState.measure.bodyMediumHeight + 16,
                              ),
                              minVerticalPadding: 0,
                              padding: EdgeInsets.only(
                                left: 12.ap,
                                right: 16.ap,
                              ),
                              delegate: RadioDelegate(
                                onTab: () {
                                  _handleChangeMode(item);
                                },
                                value: item,
                              ),
                              title: Text(
                                Intl.message(item.name),
                                style: Theme.of(
                                  context,
                                ).textTheme.bodyMedium?.toSoftBold,
                              ),
                            ),
                        ],
                      );
                    },
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class OutboundModeV2 extends StatelessWidget {
  const OutboundModeV2({super.key});

  void _handleChangeMode(Mode mode) {
    globalState.container.read(setupActionProvider.notifier).changeMode(mode);
  }

  Color _getTextColor(BuildContext context, Mode mode) {
    return switch (mode) {
      Mode.rule => context.colorScheme.onSecondaryContainer,
      Mode.global => context.colorScheme.onPrimaryContainer,
      Mode.direct => context.colorScheme.onTertiaryContainer,
    };
  }

  String _getModeTitle(Mode mode) {
    return switch (mode) {
      Mode.rule => '⚡ Умный',
      Mode.global => '🌍 Полный',
      Mode.direct => '🚫 Без VPN',
    };
  }

  @override
  Widget build(BuildContext context) {
    final height = getWidgetHeight(1);
    return SizedBox(
      height: height,
      child: CommonCard(
        child: Consumer(
          builder: (_, ref, _) {
            final mode = ref.watch(
              patchClashConfigProvider.select((state) => state.mode),
            );
            final thumbColor = switch (mode) {
              Mode.rule => context.colorScheme.secondaryContainer,
              Mode.global => globalState.theme.darken3PrimaryContainer,
              Mode.direct => context.colorScheme.tertiaryContainer,
            };
            return Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              constraints: const BoxConstraints.expand(),
              child: CommonTabBar<Mode>(
                children: Map.fromEntries(
                  Mode.values.map(
                    (item) => MapEntry(
                      item,
                      Container(
                        clipBehavior: Clip.antiAlias,
                        alignment: Alignment.center,
                        decoration: const BoxDecoration(),
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
                        child: Text(
                          _getModeTitle(item),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: Theme.of(context)
                              .textTheme
                              .titleSmall
                              ?.adjustSize(1)
                              .copyWith(
                                fontWeight: FontWeight.w600,
                                color: item == mode
                                    ? _getTextColor(context, item)
                                    : null,
                              ),
                        ),
                      ),
                    ),
                  ),
                ),
                padding: EdgeInsets.zero,
                groupValue: mode,
                onValueChanged: (value) {
                  if (value == null) {
                    return;
                  }
                  _handleChangeMode(value);
                },
                thumbColor: thumbColor,
              ),
            );
          },
        ),
      ),
    );
  }
}

