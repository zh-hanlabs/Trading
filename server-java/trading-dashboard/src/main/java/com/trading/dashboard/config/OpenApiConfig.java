package com.trading.dashboard.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * OpenAPI 3 / Swagger 文档配置
 */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI tradingOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("A股投研看板中台 API")
                        .version("1.0.0")
                        .description("提供全市场板块资金流多维排行与高频日内时序数据查询接口")
                        .contact(new Contact().name("Trading Co-pilot")));
    }
}
