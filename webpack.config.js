const glob = require("glob");
const path = require('path');
const webpack = require('webpack');

const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlInlineScriptWebpackPlugin = require('html-inline-script-webpack-plugin');
const HtmlInlineCSSWebpackPlugin = require('html-inline-css-webpack-plugin').default;
const HtmlWebpackInlineSVGPlugin = require('html-webpack-inline-svg-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');

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
        publicPath: '',
    },

    module: {
        rules: [{
            test: /\.css$/i,
            use: [{
                loader: MiniCssExtractPlugin.loader,
            },
                'css-loader',
            ],
        },
        {
            test: /\.(jpe?g|png|gif|woff|woff2|eot|otf|ttf|ico)(\?[^\/]+)?$/i,
            type: 'asset/resource',
            generator: { filename: '[name][ext]' }
        },
        {
            test: /\.svg$/i,
            oneOf: [
                {
                    issuer: /\.css$/i,
                    type: 'asset/inline', // inline SVG in CSS
                },
                {
                    type: 'asset/resource', // SVG standalone
                    generator: { filename: '[name][ext]' }
                }
            ],

        },
        ],
    },

    optimization: {
        minimizer: [
            new CssMinimizerPlugin(),
            new TerserPlugin({
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
        ]
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
            inject: 'body',
        }),
        new HtmlInlineCSSWebpackPlugin(),
        new HtmlWebpackInlineSVGPlugin(),
        new HtmlInlineScriptWebpackPlugin(),
    ]
};
