"""
Check if old docs have been edited.

This takes in a dir, and hashes all of the files in it (recursively going through
sub-dirs) It compares them all to the expected output, and raises an issue if
any don't match.
"""

import hashlib
import argparse
import json
import os

hashes = """
{
    "_static/NRL_logo_RGB.jpg": "ca9dd0c048872a3d3993f01193696f6fefce52ccb521c97a1c575125130a5168",
    "_static/NRL_logo_RGB.png": "cf97a93a2795e6a291b101c5888a30880a592cd431986dfae44054fb51bde560",
    "_static/NRL_logo_sidebar.png": "1019260c631f417e50d8bad2d76280221f31f7f739d69214ee6d1c5f10541778",
    "_static/NRL_logo_sidebar_Reverse.png": "63c2a9d2d7f97e2ad3581816436cdac5db27fccd9f290d5798c3e8ea382cf4d3",
    "_static/index_api.png": "abb3433fac668a15d819915161418fe3d3ae8079cb659d34b8aa0f9784b13783",
    "_static/index_contribute.png": "437758b0bf438b3c7170f1896c534b3a3b99fcd83dbe9ff6ce0cdf0583e4fa80",
    "_static/index_getting_started.png": "5669e6c82a106c8b6b27b92dcf5e373447004a794d59716c3320b2d4ce0d0678",
    "_static/index_user_guide.png": "714a9e3c818ac51e7be6a1c3ae3eb6a7001245f33e8560c32607d91d261764a4",
    "_static/nrlicon.ico": "e5743427141400f672c18fd164483a505e6696253ee0e106998e332f3bae8ffa",
    "_static/set_width.css": "71fb982c4c15d7eb1623b3cb4d5d427474974f5547b554f773739e6917422521",
    "_templates/conf_PKG.py": "75ef0826c4b3f72de29939bc8ca407179d8d3503e5e318da1435dabd8da4019d",
    "_templates/geoips_footer.html": "0ef13b998f758e5763248bd6553a45320c92e76daef6b46a95092c3b936b223b",
    "_templates/index_PKG.html": "7dc3283736f79257c7e70fb212966bbe48577348075bfc5709da13b868a5b4a6",
    "contact/aboutus.rst": "2cd301c43b3a6d6d03e666f1aa4750c06ebefa1ddb4398264ce531f6d63a2e8c",
    "contact/index.rst": "99002660c40c6eb04028809ca4d3bfcdddb1984d5f86edd6db68f1fd22cdad2b",
    "devguide/build_docs.rst": "e443648ca84a8da446d3331d346e4a8bf767bdd2ab35d31ab5275529dfca9476",
    "devguide/contributors.rst": "846b635e4e2182eba828c2c6980bc1333707852c4af54fbac21014d1a3c9964e",
    "devguide/dev_setup.rst": "5b628dcdbb54a1f060b744872d425d1e4759edea52d7c6d1e6e35de108206d9f",
    "devguide/documentation_strategy.rst": "ed262cce73f59c862d45d81b4afc427e82f3af50c4acd5af45aed5c9cca3eebb",
    "devguide/git_workflow.rst": "898f59b15482dc712bf654cbfdc0e778f37f7e5d7384ce30e726616d9884e388",
    "devguide/index.rst": "3754a3a1867856f952ae82f5866af5bf1b65d350b374e73593dd6df8f8718cbc",
    "devguide/software_requirements_specification.rst": "71e93874db5b187e6a066d27e722ab346f073fd626cca10dcd102b858a0132cf",
    "devguide/unit_tests.rst": "de2fe2b4e663736808ee16ca9a451e7c71cf5646a4567e4638b8570bed1d81cb",
    "devguide/xarray_standards.rst": "18e56d07847e81e016bf314c64d0b98de386a8a4f936f50912b0ca595d85914f",
    "fancyhf.sty": "836745d81ddd2cdf540f7aa1c24976ad173bdca33478eccf98db64793b96dfd2",
    "geoips_api/index.rst": "8b6bf86b697d856bbf60598f9e93f634006660f7ae0e28047c3154b35cfd7903",
    "images/available_functionality/20181025_203206_WP312018_sar-spd_sentinel-1_nrcs_130kts_58p51_res1p0-cr300.png": "b4043a2e5784a9b4aaf172b53885de6f6a3f1285714923e35c512c101b6cae13",
    "images/available_functionality/20200216_124211_SH162020_smos-spd_smos_windspeed_75kts_38p84_1p0.png": "ace438b9d1830310a4c59e7104e2ff0556f8323a83b818e7dcc6533001ec1e3c",
    "images/available_functionality/20200404.080000.msg-1.seviri.Infrared-Gray.global.22p84.nesdisstar.20p0.png": "27b2ecde254be81838eafc9209ad54b864d32a8dc82b530f5822d7c430167661",
    "images/available_functionality/20200404.080000.msg-1.seviri.WV-Upper.self_register.69p07.nesdisstar.10p0.png": "59005b80aa7d81c7b670778830e3001a2c75bd626d7e2acb60f6667689aea377",
    "images/available_functionality/20200405.000000.himawari-8.ahi.Infrared-Gray.global.29p98.jma.20p0.png": "7b460447971b20eddb0e65a60f60417cf6d8585282840ba147ddcc7d6ea6cbe5",
    "images/available_functionality/20200513_215200_WP012020_amsu-b_noaa-19_89V_95kts_89p18_1p0.png": "1c5e4b32c1402d43f24fcc326110b484e367e2835c88bd2b723f7b0ef38ab831",
    "images/available_functionality/20200518_073601_IO012020_amsr2_gcom-w1_89pct_140kts_28p31_1p0.png": "b47c3c84b1f382858cf94573dfadb2f471153239a979ebbc9f48b0f6c172c438",
    "images/available_functionality/20200917.171519.GPM.gmi.89H.global.0p84.NASA.20p0.png": "6e8164b37669f3ab58effeeee2c5f1cccf716d2969bd9bb95b64916dc7e75fe5",
    "images/available_functionality/20200918.195020.goes-16.abi.Infrared-Gray.global.22p84.noaa.20p0.png": "388826e9a594a11cadcf562dd4a83b10df2d3afd60eac49877ad0e3d0b6defd7",
    "images/available_functionality/20201211.230905.ews-g.gvar.Infrared-Gray.global.33p25.noaa.20p0.png": "48e9281a43f750380dccd5e5fd84cd8c3ab21a1cd14499d775b6b89631ba617b",
    "images/available_functionality/20210104.170500.terra.modis.Infrared-Gray.global.0p63.nasa.20p0.png": "8f8dea61ae1567dc9806b2be30f56f243b4599c7ea8aa83e9e14d8f9c0dc8788",
    "images/available_functionality/20210104.201500.aqua.modis.Infrared-Gray.global.2p08.nasa.20p0.png": "e52425ed5dc009b6736ad2db3729b4edf899a08f0f2667894f592ba0737b293c",
    "images/available_functionality/20210104.201500.aqua.modis.Infrared.self_register.100p00.nasa.3p0.png": "76e769d30d94aa39a94b589e05e3a70f8e3de366ea1a65723d8931465a6da3f7",
    "images/available_functionality/20210205.080611.npp.viirs.Infrared-Gray.global.0p97.NASA.20p0.png": "61d4b7705751b19410fbc6668352445daff437b7e2ef2181542e2ab3b7d580cd",
    "images/available_functionality/20210209.074210.noaa-20.viirs.Infrared-Gray.global.2p00.NASA.20p0.png": "4745366f61744363c104148d72b76560f4b80cd517911802e5182b4ef5e9cd32",
    "images/available_functionality/20210209_074210_SH192021_viirs_jpss-1_Night-Vis-IR_130kts_100p00_1p0.png": "732af97c72f2330807742bcd0193431abf23c653b157d376bcc2b1a0385e64fb",
    "images/available_functionality/20210419_235400_WP022021_amsu-b_metop-a_183-1H_115kts_100p00_1p0.png": "cb487709fdb116fbd4a847e15b6724113bf178317ff9cf6a312a325d283e2f41",
    "images/available_functionality/20210419_235400_WP022021_amsu-b_metop-a_183-3H_115kts_100p00_1p0.png": "cde63ab51f5b582f3cd89c54b01dbcb43ad4887199c0a4c5254939b11daea893",
    "images/available_functionality/20210718.015031.goes-17.abi.Infrared-Gray.global.22p79.noaa.20p0.png": "f233354864f0250eb95ee7318b9b73dd8561234cac5cdc5f3bc2e6af377c5d91",
    "images/available_functionality/20210926_210400_WP202021_smap-spd_smap_windspeed_100kts_74p87_1p0.png": "f073671ff69b9c09ff22c9d037f5cf3a846973e64698efc59bbe0eaa4f874380",
    "images/available_functionality/20211202.080644.hy-2b.hscat.windspeed.global.6p83.knmi.20p0.png": "7cbd8acda76fbe893e8f5bc73721f7ec1d54186efe41e1389f5b4c7746e120e2",
    "images/available_functionality/20211202_084039_WP272021_hscat_hy-2b_windbarbs_95kts_97p06_1p0.png": "a6b12f4e05e3584929921d3edc8b6b563b07e63463dbac2a6f4d0948d39812c0",
    "images/available_functionality/20220209.220000.msg-4.seviri.Infrared-Gray.global.22p84.nesdisstar.20p0.png": "08b066645de1b01d764a7782152aa341948d653924c48e95ae02d898296aac52",
    "images/command_line_examples/20200918.195020.goes-16.abi.Infrared.goes16.45p56.noaa.10p0.png": "e5765455f94ebe7b02903ebbedd8ed61919a7b9541846443c5a3936d3b4fedf5",
    "images/command_line_examples/20200918_195020_AL202020_abi_goes-16_IR-BD_110kts_100p00_1p0.png": "3e7e1742c97e321423b0f8bc8acb16b0a81055204f68aef563d5ff8bd59eb24a",
    "images/command_line_examples/20200918_195020_AL202020_abi_goes-16_WV_110kts_100p00_1p0.png": "a586d08f11c989aa351ec7998f53f95f954ef4a14d9dfa6656f78bc2a275c83b",
    "images/command_line_examples/colorful_cloud_height.png": "0b5ee500e33cdb3627569a717885a28b872546663c73dea84a5702b06637a630",
    "images/command_line_examples/my_cloud_depth.png": "39f0603e8841997413f5f21334ac3ffc51e12cc713f339b66eb79f0fb3d544c9",
    "images/command_line_examples/my_cloud_top_height.png": "a7e13fd0d3db72975fe1b52d92595701e6d0db6afa9b0d05fab582c97c5d8d74",
    "images/command_line_examples/my_conus_sector.png": "a4249e10d6b33ae6e88c28e5bf871864a08dca087e33637b8a5369712d4ffc52",
    "images/command_line_examples/my_conus_sector_cth.png": "0cf1c28f176271225d81b745949a3d5193ade14a08d261d556537928bf3ad3c5",
    "images/command_line_examples/my_feature_gridline.png": "4600b8ed9372f4d4b73f7754cb36b508670f25fdc4ea6b6add40fe2464ad181c",
    "images/geoips_overview/Example_89pct_GEOTIFF_Processing_Workflow.png": "049fde5cf0f91450c3d18572d71ea1866bcb08b93202bb3dbb21605708a5d788",
    "images/geoips_overview/Example_89pct_Overlay_Processing_Workflow.png": "10dc902e7daf513278cd4f710fff8f8548c06aa447449152c6cb8b707579e3bf",
    "images/geoips_overview/Example_DEBRA_Processing_Workflow.png": "4b8c6cdf8e6721fa9361253f2600c2037da7d3313c215849e937651ac5de2e9b",
    "images/geoips_overview/Example_config_Processing_Workflow.png": "a9ad92c53828262f238b72b5dbc12b3affbefaa5b3ce5b13749e022405645378",
    "images/geoips_overview/GeoIPS_Functionality_Overview.png": "8729b76537b3fdfe218d6437fc0f158e6303be7b35273820f8d988d98c05bae3",
    "images/geoips_overview/GeoIPS_Processing_Chain.png": "0cd85aac7aff6f7f8c9da4dadf1e07a97d4da034b176270ad70a95e9d2ce4463",
    "images/geoips_overview/GeoIPS_Structure_Overview.png": "c760a335b638c5cd05607358fe18d10c368faa2dc80332895e1fb5a05b45fe80",
    "introduction/conduct.rst": "b529044790b17a584744c65241fa9e49702b32fe6d3eb915690dca504dfc063b",
    "introduction/description_geoips.rst": "3c1ef993e2f016e47a516a1ffee86ac781a41a1003dbe4a99df4c42c0794afca",
    "introduction/examples_output.rst": "3f95ef383cec81df423d12729791b9b37fa7702ec4b9f945324329859689d8f0",
    "introduction/function_summary.rst": "89983d339ec569ce3f8f774fbc1a6c8993911051599560cafb212f92903100da",
    "introduction/index.rst": "ed4bfac51225c51412085f4c15bd6f0063ba4ddc4053b486cf332c0e66b4426c",
    "releases/index.rst": "d36734d2e662d5976a2a37bdc53b0ab56f0f3e8e74aa1cce55b39f29f848c739",
    "releases/v1_10_0.rst": "81de933979425fe869a060df9ed57a85250d3128f2119142a655c7cd99b31548",
    "releases/v1_10_0a0.rst": "e4bbfb35e9e84695c2e0eff4bdb51ea4b02a466956ad128c53f6089e8a45c879",
    "releases/v1_10_0a1.rst": "068255cd284df7cd84715ffa367b6301e021ee060e8e6275e055a7e73e0f3f09",
    "releases/v1_10_0a10.rst": "024ea5e64b0002501e410507175642f3a7643c30db8b7b4e962ed47de0e2581e",
    "releases/v1_10_0a11.rst": "75f4e81962ac24f57e2f5cc68bcc41e4705c8a6edff4de9bc96593908b49b28d",
    "releases/v1_10_0a12.rst": "fdc2f0adcc67d924567c7a0b5b2e27ba85365b4893bfa3c1eab55f3860c489ae",
    "releases/v1_10_0a13.rst": "4ed51aa031e6916a5e261e5fec0c2ff64b0f54dc3ab53b745406240541404db9",
    "releases/v1_10_0a2.rst": "16a250acf036da7820b9eb5e661861970dddd616e1f092a0bc5f21b879807079",
    "releases/v1_10_0a3.rst": "bf749a02303a1002f22e81e59367e1bf7d1fae50b488fa575f47482e66cd20f3",
    "releases/v1_10_0a4.rst": "504673178d3850aabffdf492fbd4546b7a34bfc3cfdabaf8977797ff7cec344e",
    "releases/v1_10_0a5.rst": "70157a4e161b066684cdb5523d80168ed05e072d32f9de74c70af8f8ba16216c",
    "releases/v1_10_0a6.rst": "d0ffe95399b9518891408063dac164b5aa211757972bd30964c7f1beeb9769fe",
    "releases/v1_10_0a7.rst": "0b0bfbc66029ab62bd6d4f769e39b35b8486cdc60bf585680372d7ec7c76881c",
    "releases/v1_10_0a8.rst": "631568103f58637b717ddf5a330163c8b76ad5a063d0c16ff325f7945dfa9303",
    "releases/v1_10_0a9.rst": "2c1e0b2708cd4a7af56b7e5350121e10a6afd2a649361dd4e2076c76ce6688ef",
    "releases/v1_10_1.rst": "20b18a3ae0b1e3861f7a5ba3e80ec3a72fdc8b0f5fec3339e5b8e3f16408c46e",
    "releases/v1_10_2.rst": "2e7106ee132ed67ce2eb0e647a5f992ce48362ab5ae8346c8ccdf708b9783a50",
    "releases/v1_10_3.rst": "79f92f8c99b9112ebef0a9a76ffc60237cab6871112e8379dc3e2c072c84dde3",
    "releases/v1_11_0.rst": "20c63cb46dbdb1fda7fc8605f3dcd20c1c6a88df92162433bc51fe605840d425",
    "releases/v1_11_1.rst": "64cd389eb70c4d122c14476c1f019b44e8235a97b4a3f4a6dc53b62e232a7c43",
    "releases/v1_11_1a0.rst": "dcdca11d71181cb9a41e23907c126b108a9d1a5de8878945272bb19ae74cd92c",
    "releases/v1_11_2.rst": "c359cf28a6294b2b52d9ce72939f8a6737e8cfc9941a6d35b1017ba0d26f6c7b",
    "releases/v1_11_3.rst": "d1d587052d3b3d4782758460a7a3a28da5dc7f0685c5a9c11c5503b9aa4dea44",
    "releases/v1_11_3a0.rst": "3f4e1fa55faff9f872032c672f82c024fd3c884aa7d3b88eaee8812919a916f3",
    "releases/v1_11_5.rst": "045c0d5b7adfcb810198737b27c294a15b9c1803e99fad53bc667a4f7e7d4b79",
    "releases/v1_11_5a0.rst": "342fe2c850009f62752fb413843303c5cdcc6ccb11e2685fce398b2f6f9482aa",
    "releases/v1_11_6.rst": "4f0f990fbc3d3f57f07e758d679a6f17e9854893d3bb4c2db9abebb00c5ee51b",
    "releases/v1_11_7.rst": "e833bb766bd2907a93662dd943bd9614bd622d962b61991fbc61fc8922feb282",
    "releases/v1_11_7a0.rst": "cf57366f31505cfd52ca60928e66ad4487af84a9ad90ffa3483636baeb333b45",
    "releases/v1_12_0.rst": "edebc64ca6291971d41f646657b7f7cc41e64be1f3008f881aa70daf43d5b322",
    "releases/v1_12_1.rst": "68f7197a57ba349b040fbf0638691edaa594b2b353cdf860e9edb832cd68ad55",
    "releases/v1_12_2.rst": "46a72882233e6fc3adf6520ebe866a39b3ba0d8ed7724f3102eef20026b974a4",
    "releases/v1_12_2a0.rst": "322b07246fd982f03db40b352033b3eada081e7f7556fd3d2ec10339cd895699",
    "releases/v1_12_3.rst": "a3a5bb51b191543db0464f8020db543edec852ac8249bef30b9b31fa019d75cb",
    "releases/v1_13_0a0.rst": "5ad0f184f1318ffb655bb4c6b43893435edfb13093784e5ca6d976b5249a6c95",
    "releases/v1_1_13.rst": "4961b89ded96633e235c660752ab8453fdb23e51c8d4e0b79cb46bebb92a0f84",
    "releases/v1_1_14.rst": "df09f40d532ed4219b52ef9aada00f38468a9a3f3435ce3d13fcd8fc3c4a34fa",
    "releases/v1_1_15.rst": "9e465ac2736fdb5348ffd225121e79cdf865eff10b349414a3c5f507e82f3b41",
    "releases/v1_1_16.rst": "328b35b50e15c37c5651d2c37d4acbb557513a16d5a45ee9bb4e9c8cd8487b66",
    "releases/v1_1_17.rst": "ff3f605c55329a3bd52c577aab3a4924c0c77d4afee4448fccd1710f46116678",
    "releases/v1_2_0.rst": "fb5cd6f36d1817333321c743826db27aa16318a3ecfaaa069a1906fcaf20f02e",
    "releases/v1_2_1.rst": "43a6605a077fc078eb4336d67a01b68150dfa705e76171578783091a3e291741",
    "releases/v1_2_2.rst": "4b68bad44f3f7d067f59a7f9a6744300bbcad994f90a28129fc3fd936f5ac5be",
    "releases/v1_2_3.rst": "00c05e52da5f3def4cec7564ff8aa4f537d209923e8e115080632aa1f554dc36",
    "releases/v1_2_4.rst": "db6068071bb3ff376f33d40d39b8fd637b712f142286633d540e5dbf15c3f378",
    "releases/v1_2_5.rst": "e93f70321da44b9a4b728e62fe2a0ac91ffb4c47438087766924897f80cfd1b1",
    "releases/v1_3_0.rst": "e2dedce9e0122beecb6bfc035a5a0c37d46211f19ca995a8795d0b7d382ab9e3",
    "releases/v1_3_1.rst": "019d6774f57c1cb5a228ade8aee0f33b2b75a8aa99228c5cfe5d78a7c91f1989",
    "releases/v1_3_2.rst": "fe5365211a3a8685c408d60d3ce064064c6e57daa7e238b6c23c818f7f0d6c5a",
    "releases/v1_4_0.rst": "693cfd605cb642fc8812936e9b61ab0be30162eb56187e217bdd4a768253e63c",
    "releases/v1_4_1.rst": "5935d7dc92b7ee7216803d08167b7dc9638028405e64dfa38d440515b85bc4ff",
    "releases/v1_4_2.rst": "55f93e431d9d2840d33c3824414dc09bd86ff3da866e644bc60ca74743463b8f",
    "releases/v1_4_3.rst": "cc0821faa4e142d77b7f15302c8c5ea94fd71e3639389a74719bd9a93a7547d5",
    "releases/v1_4_4.rst": "4dc23f719bd291dbc5291f39b0c00794393e5a11b451b46924d9828e85752372",
    "releases/v1_4_5.rst": "81eea0bbd8cd0d5cf2a1a8d5602fa8d4875e7f59b9e1c0abc42af4d2ac984284",
    "releases/v1_4_6.rst": "d37b69923aaaef12a48565f195d86560df1c29a2744cabea6fda5c405aca271f",
    "releases/v1_4_7.rst": "a8d7d1cc29ad27b992d0f67c7ac7d87208b869a84cc72296426014177aa5f1a6",
    "releases/v1_4_8.rst": "761da35cc9582be73c9d292d2aa6aa9c04524caa05be57ab40dc0e31f16020ee",
    "releases/v1_5_0.rst": "64ef86ec957460a53d2eacf14d03df763dda9ec45bd3c6b7a92b55f813a9af1d",
    "releases/v1_5_1.rst": "c68828dd80896dfefd0a3130b6b567b123f67f60d3f746e265de2fe36ae40690",
    "releases/v1_5_2.rst": "4550c3c5628bf22b6018f87be8087ae1888012c6276480bc30af968cda4af461",
    "releases/v1_5_3.rst": "e5ab5260db633503521dae7d7bc67e970f5c88a2e34bc373f31ad2b3e87dd253",
    "releases/v1_6_0.rst": "58451675c622d91995cc79ca8cfa6dbce90be1868e3b8de621b79cd97c4534b0",
    "releases/v1_6_1.rst": "b63daf5a94a3cb36b8a233d4a0151698a3e4a7c05d3bf1096dd982ade51642fd",
    "releases/v1_6_3.rst": "9929b3fb13e02f031637d2b8bd2954a4bb6b53a847915cf072f2ac1f91fbbccf",
    "releases/v1_7_0.rst": "fc08167888f783fef1cfe5e54180e37778dff120c7fc0496f7b6870024e636a0",
    "releases/v1_8_0.rst": "6892817ac09bfc5f4cfc89e0665e7f250e8558d372dee89b1fbb27829c79c538",
    "releases/v1_8_1.rst": "ce20b0eaf22dfa703758dad554177655abc3e54eece9d4211652e741008bd24e",
    "releases/v1_9_0.rst": "44047c443fa433c8e83ee950adb65d762b414094023a5ca4a3287ce5cd2c04ee",
    "releases/v1_9_1.rst": "b14d2d12ca7845653fd7a825bfe4b563677f910984f2d73f54e636641dd1d4b4",
    "releases/v1_9_2.rst": "3dfaed2b6e9f5450d54a01abd80932f017c0ef87745a1bc30fc67427511d824a",
    "starter/expert_installation.rst": "2250d811a045562596564f03eb200ef969eba3324e492640e0a604662f7eac71",
    "starter/extending.rst": "827066787be64e193ab11c206030c64dfb01a0f86b44e2941a9e2c3ae4ddcd32",
    "starter/index.rst": "8738995ac669c8644909e3682364d481330c706891dccf4e0175f7cb660d6a11",
    "starter/installation.rst": "706ca1adacf50aa3e6883a377d8116371420e966222c498be604203d7f4947a4",
    "starter/mac_installation.rst": "008f75b7c94c63b09a6b775d000a8c678e1f25e7990b542a9285b18ea545c857",
    "starter/starter_examples.rst": "d02cb41c43a28d67c0ab1a0d0d157be530773d209caddaf75ca7efb639296b51",
    "starter/windows_installation.rst": "a36b179b3450749def0c62b2525f9cbd2e6bffc48bc1b063e1169251a86fcc5a",
    "userguide/command_line.rst": "0261b25a74c1b9d1dac3c332163ad56dc7ae4a938ba8a23da3f86350bffcc202",
    "userguide/function_list.rst": "f9933d9a1a7b9d8bc8225a9640cbc46d820108ef15d023befd2d2c4ed56bc3f5",
    "userguide/geoips_structure.rst": "98efb4ea4eb8561d5f0a1779b78118f76345cb1b3c815e32a0d354a1fd76bc9f",
    "userguide/index.rst": "1ac7c5955db324a8530662d330d6d2f6ba110b1d40b004ce3e7c97f4767af260",
    "userguide/plugin_development/algorithm.rst": "367046342f944662c881554f92d862e7aea424a2887099efde77103598db0e9d",
    "userguide/plugin_development/colormapper.rst": "2dc2191d688fb34628589d8122bf382b6875c75b11964073eaa194b83165b796",
    "userguide/plugin_development/feature_annotator.rst": "a58ca79c7e21ba4e20987f105acedd2dabd5b0c39e4441aeafacf35844ea2cd5",
    "userguide/plugin_development/gridline_annotator.rst": "324a20e8aa50c09f533aaa68afe259c942a508ec5ffd69fcd97ee2c6280bc3b3",
    "userguide/plugin_development/output_formatter.rst": "fe419a7aea7b5390e885339a01337314e0e6197f6ad74a1287ed9f4a5448ca8b",
    "userguide/plugin_development/product.rst": "a881061b4d14469c4b544cddbf81ce300e63c90b77d36f6f6a4544451689472a",
    "userguide/plugin_development/product_default.rst": "dfa6aaa3dfe23718f447f00696418474c13b7e7bb9e6a734e25f1d14c2b7b8ea",
    "userguide/plugin_development/reader.rst": "42be68b2da5969ebab060430d94f6c69073a3711091e94648a2bfbad767d3cbb",
    "userguide/plugin_development/static_sector.rst": "993cdcdcb5abd3b2f5337587a40fe1f3a5080174a55b9f8db824c0434043245f",
    "userguide/plugin_extend.rst": "b0cb8a05209df0166fb6db66723048b3701f18d5598f7676230932dd5220e866",
    "userguide/plugin_registries.rst": "3440f4f64b9ee5dba79c62ccccaeefdeda42fa2778855ef69527e0daf150bebe",
    "yaml/20200918.195020.goes-16.Visible_latitude_longitude.tc2020al20teddy.nc.yaml": "3c55450060c18d783d6507f6618d16f2126f916b56bc562a6d739824142dc726",
    "yaml/20200918_195020_AL202020_abi_goes-16_IR-BD_110kts_100p00_1p0.png.yaml": "d0321ab5302abcf6bbea06853ed99f6fe78970d0c97e7335c8bc62177a8749a3",
    "yaml/20200918_195020_AL202020_abi_goes-16_WV_110kts_100p00_1p0.png.yaml": "24dff6c0c27490f5f6ba6fb33a97e42d43109fb5c7efacdb74537a70aa07f7fb",
    "yaml/abi_test.yaml": "ad6df55b7500aba6f3d6fd4e78ae3ab8af670b933240a842b184c78c3c20b1ea"
}
"""  # noqa: E501


def hash_file(file_path):
    """Return the SHA-256 hash of the file at the given path."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_str(string):
    """Return the SHA-256 hash of the file at the given path."""
    sha256 = hashlib.sha256()
    sha256.update(string.encode("utf-8"))
    return sha256.hexdigest()


def hash_directory(directory_path):
    """Recursively hash all dir files return hashes in a dict.

    Ignores any files in docs/releases or docs/new-docs and
    docs/source/_templates/conf_PKG.py.
    """
    file_hashes = []
    for root, _, files in os.walk(directory_path):
        for file in sorted(files):
            file_path = os.path.join(root, file)
            if "new-docs" in file_path or "releases" in file_path:
                continue
            if file == "conf_PKG.py":
                continue
            file_hash = hash_file(file_path)
            relative_path = os.path.relpath(file_path, directory_path)
            file_hashes.append((relative_path, file_hash))

    # Sort by file path to ensure consistent order
    file_hashes.sort()

    # Prepare the output dictionary
    output = {path: hash for path, hash in file_hashes}

    return output


def main():
    """Handle CLI usage."""
    parser = argparse.ArgumentParser(
        description="Hash all files in a directory recursively and print the directory "
        + "structure hash in JSON format."
    )
    parser.add_argument("directory", type=str, help="Path to the directory to hash")
    args = parser.parse_args()

    directory_path = args.directory

    if not os.path.isdir(directory_path):
        print(f"Error: {directory_path} is not a valid directory.")
        return

    directory_hash = hash_directory(directory_path)

    correct_hashes = json.loads(hashes)

    bad = []
    for key in directory_hash.keys():
        try:
            if not correct_hashes[key] == directory_hash[key]:
                bad.append(key)
        except KeyError:
            bad.append(key)

    if not bad == []:
        print("Old docs have changed. :(")
        print(len(bad), "hashes have changed")
        print("These are the sad hashes:")
        for baddie in bad:
            print(baddie)

        print("\n\n\n\nThese are all the hashes:")
        print(json.dumps(directory_hash, indent=4))
        exit(1)


if __name__ == "__main__":
    main()
