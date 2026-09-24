import 'dart:convert';

import 'package:http/http.dart' as http;

class ApiException implements Exception {
  const ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;
}

abstract interface class ApiClient {
  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, String>? queryParameters,
  });
}

/// Minimal HTTP client for future authenticated API calls.
/// Repositories are the only layer that should depend on this abstraction.
class HttpApiClient implements ApiClient {
  HttpApiClient({
    required this.baseUrl,
    this.headers = const {},
    http.Client? client,
  }) : _client = client ?? http.Client();

  final String baseUrl;
  final Map<String, String> headers;
  final http.Client _client;

  @override
  Future<Map<String, dynamic>> get(
    String path, {
    Map<String, String>? queryParameters,
  }) async {
    if (baseUrl.isEmpty) {
      throw const ApiException('API_BASE_URL has not been configured');
    }
    try {
      final uri = Uri.parse(baseUrl).resolve(path).replace(
            queryParameters: queryParameters,
          );
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json', ...headers})
          .timeout(const Duration(seconds: 15));
      final body = response.body;
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          _errorMessage(body) ?? 'Request failed',
          statusCode: response.statusCode,
        );
      }
      final decoded = jsonDecode(body);
      if (decoded is! Map<String, dynamic>) {
        throw const ApiException('Unexpected API response');
      }
      return decoded;
    } on http.ClientException {
      throw const ApiException('Unable to reach the server');
    } on FormatException {
      throw const ApiException('Unexpected API response');
    }
  }

  String? _errorMessage(String body) {
    try {
      final decoded = jsonDecode(body);
      final detail = decoded is Map<String, dynamic> ? decoded['detail'] : null;
      if (detail is Map<String, dynamic> && detail['message'] is String) {
        return detail['message'] as String;
      }
    } on FormatException {
      return null;
    }
    return null;
  }
}
