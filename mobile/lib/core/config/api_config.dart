class ApiConfig {
  const ApiConfig._();

  static const baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: '',
  );

  /// Optional development-only request scope for the current backend milestone.
  /// It is not an authentication credential and will be replaced by auth headers.
  static const developmentUserId = String.fromEnvironment(
    'API_DEVELOPMENT_USER_ID',
    defaultValue: '',
  );
}
