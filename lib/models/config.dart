import 'package:fl_clash/common/common.dart';
import 'package:fl_clash/enum/enum.dart';
import 'package:flutter/material.dart';
import 'package:freezed_annotation/freezed_annotation.dart';

import 'models.dart';

part 'generated/config.freezed.dart';
part 'generated/config.g.dart';

const defaultBypassDomain = [
  '*zhihu.com',
  '*zhimg.com',
  '*jd.com',
  '100ime-iat-api.xfyun.cn',
  '*360buyimg.com',
  'localhost',
  '*.local',
  '127.*',
  '10.*',
  '172.16.*',
  '172.17.*',
  '172.18.*',
  '172.19.*',
  '172.2*',
  '172.30.*',
  '172.31.*',
  '192.168.*',
];

const defaultAppSettingProps = AppSettingProps();
const defaultVpnProps = VpnProps();
const defaultNetworkProps = NetworkProps();
const defaultProxiesStyleProps = ProxiesStyleProps();
const defaultWindowProps = WindowProps();
const defaultAccessControlProps = AccessControlProps();
const defaultThemeProps = ThemeProps(primaryColor: defaultPrimaryColor);

const List<DashboardWidget> defaultDashboardWidgets = [
  DashboardWidget.networkSpeed,
  DashboardWidget.systemProxyButton,
  DashboardWidget.tunButton,
  DashboardWidget.outboundMode,
  DashboardWidget.networkDetection,
  DashboardWidget.trafficUsage,
  DashboardWidget.intranetIp,
];

List<DashboardWidget> dashboardWidgetsSafeFormJson(
  List<dynamic>? dashboardWidgets,
) {
  try {
    return dashboardWidgets
            ?.map((e) => $enumDecode(_$DashboardWidgetEnumMap, e))
            .toList() ??
        defaultDashboardWidgets;
  } catch (_) {
    return defaultDashboardWidgets;
  }
}

@freezed
abstract class AppSettingProps with _$AppSettingProps {
  const factory AppSettingProps({
    String? locale,
    @Default(defaultDashboardWidgets)
    @JsonKey(fromJson: dashboardWidgetsSafeFormJson)
    List<DashboardWidget> dashboardWidgets,
    @Default(false) bool onlyStatisticsProxy,
    @Default(false) bool autoLaunch,
    @Default(false) bool silentLaunch,
    @Default(false) bool autoRun,
    @Default(false) bool openLogs,
    @Default(true) bool closeConnections,
    @Default(defaultTestUrl) String testUrl,
    @Default(true) bool isAnimateToPage,
    @Default(true) bool autoCheckUpdate,
    @Default(false) bool showLabel,
    @Default(false) bool disclaimerAccepted,
    @Default(false) bool crashlyticsTip,
    @Default(false) bool crashlytics,
    @Default(true) bool minimizeOnExit,
    @Default(false) bool hidden,
    @Default(false) bool developerMode,
    @Default(RestoreStrategy.compatible) RestoreStrategy restoreStrategy,
    @Default(true) bool showTrayTitle,
    @Default('') String customUserAgent,
  }) = _AppSettingProps;

  factory AppSettingProps.fromJson(Map<String, Object?> json) =>
      _$AppSettingPropsFromJson(json);

  factory AppSettingProps.safeFromJson(Map<String, Object?>? json) {
    try {
      return json == null
          ? defaultAppSettingProps
          : AppSettingProps.fromJson(json);
    } catch (_) {
      return defaultAppSettingProps;
    }
  }
}

const List<String> defaultRussianBypassPackages = [
  'ru.sberbankmobile',
  'ru.sberbank.sberid',
  'ru.sberbank.investor',
  'ru.tinkoff',
  'ru.tinkoff.investments',
  'ru.vtb.mbb',
  'ru.vtb.invest',
  'ru.alfabank.mobile',
  'ru.alfabank.investments',
  'ru.gazprombank.android',
  'ru.sovcomcard.halva',
  'ru.raiffeisennews',
  'ru.ozon.fintech',
  'ru.yandex.pay',
  'ru.psbank.morpheus',
  'ru.rshb.subway',
  'ru.uralsib.bank',
  'ru.mts.money',
  'ru.pochtabank.faktura',
  'ru.nspk.sbpay',
  'ru.nspk.mirpay',
  'ru.rostel',
  'ru.gosuslugi.app',
  'ru.gosuslugi.pos',
  'ru.gosuslugi.goskey',
  'ru.gosuslugi.auto',
  'ru.gosuslugi.culture',
  'ru.nalog.nalogfl',
  'ru.fnslabs.selfemployed',
  'ru.mos.app',
  'ru.mos.transport',
  'ru.mos.parking',
  'ru.fss.navigator',
  'ru.pfr.mobile',
  'com.wildberries.ru',
  'ru.ozon.app.android',
  'com.avito.android',
  'ru.sberbank.megamarket',
  'ru.yandex.market',
  'ru.instamart',
  'ru.samokat',
  'com.ru.dixy',
  'ru.winelab',
  'ru.pyaterochka.app',
  'ru.perekrestok.app',
  'ru.magnit.app',
  'ru.lenta.app',
  'ru.vkusvill',
  'ru.krasnoeibeloe.app',
  'ru.bristol.app',
  'ru.detmir.app',
  'ru.dns.shop',
  'ru.mvideo.app',
  'ru.yandex.taxi',
  'ru.yandex.yandexmaps',
  'ru.yandex.yandexnavi',
  'ru.dublgis.2gis',
  'ru.citydrive',
  'ru.delimobil',
  'ru.belkacar',
  'ru.yandex.mobile.drive',
  'ru.rzd.pass',
  'ru.russianpost.app',
  'ru.cdek.mobile',
  'ru.boxberry.app',
  'ru.mts.selfcare',
  'ru.megafon.ml',
  'ru.tele2.mytele2',
  'ru.beeline.services',
  'ru.yota.android',
  'ru.rt.life',
  'ru.ertelecom.domru',
  'com.vkontakte.android',
  'ru.vk.video',
  'ru.vk.music',
  'ru.vk.calls',
  'ru.rutube.app',
  'ru.ok.android',
  'ru.kinopoisk',
  'ru.yandex.music',
  'ru.sberzvuk',
  'ru.premier',
  'tv.okko.android',
  'ru.mts.kion',
  'ru.rt.video.app',
  'ru.ivi.client',
  'ru.pikabu.android',
  'ru.habr.android',
];

@freezed
abstract class AccessControlProps with _$AccessControlProps {
  const factory AccessControlProps({
    @Default(true) bool enable,
    @Default(AccessControlMode.rejectSelected) AccessControlMode mode,
    @Default([]) List<String> acceptList,
    @Default(defaultRussianBypassPackages) List<String> rejectList,
    @Default(AccessSortType.none) AccessSortType sort,
    @Default(true) bool isFilterSystemApp,
    @Default(true) bool isFilterNonInternetApp,
  }) = _AccessControlProps;

  factory AccessControlProps.fromJson(Map<String, Object?> json) =>
      _$AccessControlPropsFromJson(json);
}

extension AccessControlPropsExt on AccessControlProps {
  List<String> get currentList => switch (mode) {
    AccessControlMode.acceptSelected => acceptList,
    AccessControlMode.rejectSelected => rejectList,
  };

  AccessControlProps copyWithNewList(List<String> value) => switch (mode) {
    AccessControlMode.acceptSelected => copyWith(acceptList: value),
    AccessControlMode.rejectSelected => copyWith(rejectList: value),
  };
}

@freezed
abstract class WindowProps with _$WindowProps {
  const factory WindowProps({
    @Default(0) double width,
    @Default(0) double height,
    double? top,
    double? left,
  }) = _WindowProps;

  factory WindowProps.fromJson(Map<String, Object?>? json) =>
      json == null ? const WindowProps() : _$WindowPropsFromJson(json);
}

extension WindowPropsExt on WindowProps {
  Size get _size => Size(width, height);

  Size get size => _size.isEmpty ? const Size(680, 580) : _size;
}

@freezed
abstract class VpnProps with _$VpnProps {
  const factory VpnProps({
    @Default(true) bool enable,
    @Default(true) bool systemProxy,
    @Default(false) bool ipv6,
    @Default(true) bool allowBypass,
    @Default(false) bool dnsHijacking,
    @Default(defaultAccessControlProps) AccessControlProps accessControlProps,
  }) = _VpnProps;

  factory VpnProps.fromJson(Map<String, Object?>? json) =>
      json == null ? defaultVpnProps : _$VpnPropsFromJson(json);
}

@freezed
abstract class NetworkProps with _$NetworkProps {
  const factory NetworkProps({
    @Default(true) bool systemProxy,
    @Default(defaultBypassDomain) List<String> bypassDomain,
    @Default(RouteMode.config) RouteMode routeMode,
    @Default(true) bool autoSetSystemDns,
    @Default(false) bool appendSystemDns,
  }) = _NetworkProps;

  factory NetworkProps.fromJson(Map<String, Object?>? json) =>
      json == null ? const NetworkProps() : _$NetworkPropsFromJson(json);
}

@freezed
abstract class ProxiesStyleProps with _$ProxiesStyleProps {
  const factory ProxiesStyleProps({
    @Default(ProxiesType.tab) ProxiesType type,
    @Default(ProxiesSortType.none) ProxiesSortType sortType,
    @Default(ProxiesLayout.standard) ProxiesLayout layout,
    @Default(ProxiesIconStyle.standard) ProxiesIconStyle iconStyle,
    @Default(ProxyCardType.expand) ProxyCardType cardType,
  }) = _ProxiesStyleProps;

  factory ProxiesStyleProps.fromJson(Map<String, Object?>? json) => json == null
      ? defaultProxiesStyleProps
      : _$ProxiesStylePropsFromJson(json);
}

@freezed
abstract class TextScale with _$TextScale {
  const factory TextScale({
    @Default(false) bool enable,
    @Default(1.0) double scale,
  }) = _TextScale;

  factory TextScale.fromJson(Map<String, Object?> json) =>
      _$TextScaleFromJson(json);
}

@freezed
abstract class ThemeProps with _$ThemeProps {
  const factory ThemeProps({
    int? primaryColor,
    @Default(defaultPrimaryColors) List<int> primaryColors,
    @Default(ThemeMode.dark) ThemeMode themeMode,
    @Default(DynamicSchemeVariant.content) DynamicSchemeVariant schemeVariant,
    @Default(false) bool pureBlack,
    @Default(TextScale()) TextScale textScale,
  }) = _ThemeProps;

  factory ThemeProps.fromJson(Map<String, Object?> json) =>
      _$ThemePropsFromJson(json);

  factory ThemeProps.safeFromJson(Map<String, Object?>? json) {
    if (json == null) {
      return defaultThemeProps;
    }
    try {
      return ThemeProps.fromJson(json);
    } catch (_) {
      return defaultThemeProps;
    }
  }
}

@freezed
abstract class Config with _$Config {
  const factory Config({
    int? currentProfileId,
    @Default(false) bool overrideDns,
    @Default([]) List<HotKeyAction> hotKeyActions,
    @JsonKey(fromJson: AppSettingProps.safeFromJson)
    @Default(defaultAppSettingProps)
    AppSettingProps appSettingProps,
    DAVProps? davProps,
    @Default(defaultNetworkProps) NetworkProps networkProps,
    @Default(defaultVpnProps) VpnProps vpnProps,
    @JsonKey(fromJson: ThemeProps.safeFromJson) required ThemeProps themeProps,
    @Default(defaultProxiesStyleProps) ProxiesStyleProps proxiesStyleProps,
    @Default(defaultWindowProps) WindowProps windowProps,
    @Default(defaultClashConfig) PatchClashConfig patchClashConfig,
    @Default([]) List<String> excludeSSIDs,
  }) = _Config;

  factory Config.fromJson(Map<String, Object?> json) => _$ConfigFromJson(json);

  factory Config.realFromJson(Map<String, Object?>? json) {
    if (json == null) {
      return const Config(themeProps: defaultThemeProps);
    }
    return _$ConfigFromJson(json);
  }
}
