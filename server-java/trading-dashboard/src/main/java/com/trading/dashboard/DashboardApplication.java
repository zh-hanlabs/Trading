package com.trading.dashboard;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 看板中台微服务启动类 (只读数据中台 :8081)
 */
@SpringBootApplication
@MapperScan("com.trading.dashboard.mapper")
public class DashboardApplication {

    public static void main(String[] args) {
        SpringApplication.run(DashboardApplication.class, args);
    }
}
