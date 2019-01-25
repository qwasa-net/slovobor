const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const glob = require("glob");
const path = require('path');
const webpack = require('webpack');

const HtmlWebpackInlineSourcePlugin = require('html-webpack-inline-source-plugin');
const HtmlWebpackInlineSVGPlugin = require('html-webpack-inline-svg-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin')

const TerserPlugin = require('terser-webpack-plugin');
const OptimizeCSSAssetsPlugin = require('optimize-css-assets-webpack-plugin');
const getLogger = require('webpack-log');
const log = getLogger({ name: 'webpack-batman' });

const env = process.env.NODE_ENV || 'none';

const YANDEX_METRIKA_ID = process.env.YANDEX_METRIKA_ID || 0;
const GOOGLE_TRACKING_ID = process.env.GOOGLE_TRACKING_ID || 0;
const WEB_API_URL = process.env.WEB_API_URL || "'/q'";

module.exports = {

    mode: env,

    entry: { 'slovobor': './slovobor/web/entry.js' },

    output: {
        path: path.resolve('./www/'),
        filename: '[name].js'
    },

    module: {
        rules: [{
            test: /\.css$/i,
            use: [{
                loader: MiniCssExtractPlugin.loader,
                options: { minimize: true },
            },
                'css-loader',
            ],
        },
        {
            test: /\.(jpe?g|png|gif|woff|woff2|eot|otf|ttf|ico)(\?[^\/]+)?$/i,
            loader: 'file-loader',
            options: { name: '[name].[ext]', },
        },
        {
            test: /\.svg$/i,
            oneOf: [{
                issuer: /\.css$/i,
                loader: 'url-loader', // SVG in CSS
                options: { encoding: 'base64' }
            },
            {
                loader: 'file-loader', // SVG standalone
                options: { name: '[name].[ext]', },
            }
            ],

        },
        ],
    },

    optimization: {
        minimizer: [
            new TerserPlugin({
                cache: false,
                terserOptions: {
                    toplevel: true,
                    keep_classnames: true,
                    keep_fnames: true,
                    compress: {
                        dead_code: true,
                        drop_console: true,
                        passes: 1,
                        evaluate: false,
                        inline: false,
                        conditionals: false,
                        comparisons: false,
                        keep_classnames: true,
                        keep_fnames: true,
                        unused: false,
                        warnings: true,
                        collapse_vars: false,
                        reduce_vars: false
                    },
                    output: { beautify: false }
                },
            }),
            new OptimizeCSSAssetsPlugin({})
        ],
    },

    plugins: [
        new MiniCssExtractPlugin({
            filename: '[name].css',
        }),
        new webpack.DefinePlugin({
            "YANDEX_METRIKA_ID": YANDEX_METRIKA_ID,
            "GOOGLE_TRACKING_ID": GOOGLE_TRACKING_ID,
            "WEB_API_URL": WEB_API_URL
        }),
        new HtmlWebpackPlugin({
            filename: 'index.html',
            inlineSource: '.(js|css|svg)$',
            template: 'slovobor/web/slovobor.html',
        }),
        new HtmlWebpackInlineSourcePlugin(),
        new HtmlWebpackInlineSVGPlugin(),
    ]
};
