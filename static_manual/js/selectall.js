                        $(document).ready(function(){
                        $('.selectall').click(function(){
                            if ($(this).is(':checked')){
                                $('.sub-check1').prop("checked",true);
                                $('.sub-check1 + span').addClass("required");
                                $('.sub-check1').prop("disabled", false);
                                $(".sub-check1").prop('required',true);
                                $(".sub-check").prop('checked', $(this).prop("checked"));
                                //$('').attr('checked', true);
                            } else {
                                $(".sub-check1").prop('checked',false);
                                $('.sub-check1 + span').removeClass("required");
                                $('.sub-check1').prop("disabled", true);
                                $(".sub-check1").prop('required',false);
                                $(".sub-check").prop('checked',false);
                                
                                //$('.sub-check').attr('checked', false);
                            }
                        });
                        $('.basic').click(function(){
                            if ($(this).is(':checked')){
                                $(".basic-surname").prop('checked',true);
                                $(".basic-name").prop('checked', $(this).prop("checked"));
                                $('.basic-surname').prop("disabled", false);
                                $(".basic-surname").prop('required',true);
                                $('.basic-surname').addClass("required");
                                //$('').attr('checked', true);
                                // $('.basicreq + span').prop("checked,false");
                            } else {
                                $(".basic-name").prop('checked',false);
                                $('.basic-surname + span').removeClass("required");
                                $('.basic-surname').prop("disabled", true);
                                $(".basic-surname").prop('required',false);
                                $('.basic-surname').addClass("required");

                                $(".basic-surname").prop('checked',false);
                                //$('.sub-check').attr('checked', false);
                            }
                        });

                        $('.company').click(function(){
                            if ($(this).is(':checked')){
                                $(".companyreq").prop('checked',true);
                                $('.companyreq').prop("disabled", false);
                                $(".companyreq").prop('required',true);
                                $('.companyreq').addClass("required");

                                $(".company-name").prop('checked', $(this).prop("checked"));
                                //$('').attr('checked', true);
                                // $('.basicreq + span').prop("checked,false");
                            } else {
                                $(".company-name").prop('checked',false);
                                $('.companyreq + span').removeClass("required");
                                $('.companyreq').prop("disabled", true);
                                $(".companyreq").prop('required',false);
                                $(".companyreq").prop('checked',false);
                                //$('.sub-check').attr('checked', false);
                            }
                        });

                        
                        $('.option').click(function(){
                            if ($(this).is(':checked')){
                                $('.optionreq').prop("checked",true);
                                $('.optionreq + span').addClass("required");
                                $('.optionreq').prop("disabled", false);
                                $(".optionreq").prop('required',true);
                                $(".option-name").prop('checked', $(this).prop("checked"));
                                //$('').attr('checked', true);
                            } else {
                                $('.optionreq').prop("checked",false);
                                $('.optionreq').prop("disabled", true);
                                $(".optionreq").prop('required',false);
                                $('.optionreq + span').removeClass("required");
                                $(".option-name").prop('checked',false);
                                // $('.sub-check').attr('checked', false);
                            }
                        });
                        
                        $('.event-info').click(function(){
                            if ($(this).is(':checked')){
                                $('.eventreq').prop("checked",true);
                                $('.eventreq + span').addClass("required");
                                $('.eventreq').prop("disabled", false);
                                $(".eventreq").prop('required',true);
                                $(".event-name").prop('checked', $(this).prop("checked"));
                                //$('').attr('checked', true);
                            } else {
                                $(".eventreq").prop('checked',false);
                                $('.eventreq + span').removeClass("required");
                                $('.eventreq').prop("disabled", true);
                                $(".eventreq").prop('required',false);
                                $(".event-name").prop('checked',false);
                                //$('.sub-check').attr('checked', false);
                            }
                        });
                        });
